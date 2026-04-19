"""AI chat service — conversation memory in Redis + retrieval augmentation
over user DNA, watch history, watchlist, and content catalog.

The chatbot answers questions like:
  - "what should I watch tonight?"
  - "something funny under 2 hours"
  - "summarize my taste"
  - "what did I think of <title>?"
"""
import json
import os
import uuid
from typing import Any, AsyncGenerator

import httpx
from loguru import logger
from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.llm import get_llm
from models.content import Content
from models.rating import Rating
from models.user import User
from models.watch_history import WatchHistory


MAX_TURNS = 10
VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


class ChatService:
    def __init__(self, session: AsyncSession, redis):
        self.s = session
        self.redis = redis

    def _history_key(self, user_id: uuid.UUID) -> str:
        return f"chat:{user_id}"

    async def history(self, user_id: uuid.UUID) -> list[dict]:
        raw = await self.redis.get(self._history_key(user_id))
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    async def append(self, user_id: uuid.UUID, role: str, content: str) -> None:
        turns = await self.history(user_id)
        turns.append({"role": role, "content": content})
        turns = turns[-MAX_TURNS * 2 :]
        await self.redis.set(self._history_key(user_id), json.dumps(turns), ex=60 * 60 * 24)

    async def clear(self, user_id: uuid.UUID) -> None:
        await self.redis.delete(self._history_key(user_id))

    async def get_or_create_profile(self, user_id: uuid.UUID):
        from models.chat import UserChatProfile
        res = await self.s.execute(select(UserChatProfile).where(UserChatProfile.user_id == user_id))
        p = res.scalar_one_or_none()
        if p is None:
            p = UserChatProfile(user_id=user_id)
            self.s.add(p)
            await self.s.commit()
            await self.s.refresh(p)
        return p

    async def record_feedback(self, user_id: uuid.UUID, turn_index: int, user_msg: str, assistant_msg: str, feedback: int) -> None:
        from models.chat import ChatFeedback, UserChatProfile
        self.s.add(ChatFeedback(
            user_id=user_id, turn_index=turn_index,
            user_message=user_msg, assistant_message=assistant_msg,
            feedback=feedback,
        ))
        profile = await self.get_or_create_profile(user_id)
        if feedback > 0:
            profile.positive_count += 1
        else:
            profile.negative_count += 1
        # Adaptive tuning: if user keeps downvoting, shorten and soften
        total = profile.positive_count + profile.negative_count
        if total >= 5:
            ratio = profile.negative_count / max(total, 1)
            if ratio > 0.6:
                profile.preferred_reply_length = "short"
                profile.preferred_tone = "concise"
            elif ratio < 0.2:
                profile.preferred_reply_length = "medium"
                profile.preferred_tone = "friendly"
        await self.s.commit()

    async def _context(self, user: User) -> str:
        dna = {d: round(float(getattr(user, f"dna_{d}")), 2) for d in VIBE_DIMS}

        history_rows = (await self.s.execute(
            select(WatchHistory, Content)
            .join(Content, Content.id == WatchHistory.content_id)
            .where(WatchHistory.user_id == user.id)
            .order_by(desc(WatchHistory.last_watched_at)).limit(10)
        )).all()
        history_parts = [
            f"{c.title} ({c.release_year}, {round(h.watch_pct * 100)}% watched)"
            for h, c in history_rows
        ]

        rating_rows = (await self.s.execute(
            select(Rating, Content).join(Content, Content.id == Rating.content_id)
            .where(Rating.user_id == user.id).order_by(desc(Rating.rated_at)).limit(5)
        )).all()
        rating_parts = [
            f"{c.title}: {r.rating}/5" + (f" (felt {r.mood_tag})" if r.mood_tag else "")
            for r, c in rating_rows
        ]

        # Candidate pool: top 20 by popularity the user hasn't watched
        pool_rows = (await self.s.execute(text("""
            SELECT c.title, c.type, c.release_year, c.duration_seconds, c.description,
                   c.mood_chill_tense, c.mood_light_thoughtful, c.completion_rate, c.id
            FROM content c
            WHERE c.is_active = true
              AND NOT EXISTS (
                  SELECT 1 FROM watch_history w
                  WHERE w.user_id = :uid AND w.content_id = c.id
              )
            ORDER BY c.popularity_score DESC NULLS LAST
            LIMIT 30
        """), {"uid": str(user.id)})).mappings().all()
        pool_parts = [
            f"- {p['title']} ({p['release_year']}, {p['type']}, {round((p['duration_seconds'] or 0)/60)}min, "
            f"finish_rate={round(float(p['completion_rate'] or 0)*100)}%, "
            f"mood=[tense:{round(float(p['mood_chill_tense'] or 0.5),2)}, thoughtful:{round(float(p['mood_light_thoughtful'] or 0.5),2)}]): "
            f"{(p['description'] or '')[:140]}"
            for p in pool_rows
        ]

        return (
            f"VIEWER PROFILE:\n"
            f"- Display name: {user.display_name}\n"
            f"- Taste DNA (0..1 per dim): {dna}\n"
            f"- Recently watched: {'; '.join(history_parts) or 'nothing yet'}\n"
            f"- Recent ratings: {'; '.join(rating_parts) or 'none'}\n\n"
            f"CATALOG CANDIDATES (unwatched, popularity-ranked):\n" + "\n".join(pool_parts)
        )

    async def stream(self, user: User, message: str) -> AsyncGenerator[str, None]:
        llm = get_llm()
        await self.append(user.id, "user", message)
        profile = await self.get_or_create_profile(user.id)

        if not llm.enabled:
            reply = (
                "The chat LLM isn't configured on the server. Add an API key "
                "(OPENROUTER_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY) "
                "to `.env` and restart the API. Meanwhile, try the Explore tab for mood-based picks."
            )
            await self.append(user.id, "assistant", reply)
            for tok in reply.split(" "):
                yield tok + " "
            return

        context = await self._context(user)
        prior = await self.history(user.id)
        length_cap = {"short": 80, "medium": 180, "long": 320}.get(profile.preferred_reply_length, 180)
        tone_hint = {
            "friendly": "Tone: warm, a little opinionated.",
            "concise": "Tone: brief and to the point. No fluff.",
            "formal": "Tone: polished and formal.",
        }.get(profile.preferred_tone, "Tone: warm, a little opinionated.")
        custom = f" User override: {profile.custom_system_note}." if profile.custom_system_note else ""

        system = (
            "You are RO, a personal movie & TV recommender. "
            f"{tone_hint} "
            "You have access to the viewer's taste DNA, watch history, ratings, and a catalog pool. "
            "When recommending, cite TITLES that are in the CATALOG CANDIDATES list — do not invent new titles. "
            f"Keep answers under {length_cap} words unless asked for detail. "
            f"Use plain text, no markdown headers. You can ask a short clarifying question when helpful.{custom}"
        )
        messages = [{"role": "system", "content": f"{system}\n\n{context}"}]
        # keep only last MAX_TURNS user/assistant turns (excluding the just-appended user msg which is last)
        messages.extend(prior)

        try:
            if llm.provider == "anthropic":
                async for tok in _stream_anthropic(llm, system + "\n\n" + context, prior):
                    yield tok
                    await _accumulate(self, user, tok)
            else:
                async for tok in _stream_openai_compatible(llm, messages):
                    yield tok
                    await _accumulate(self, user, tok)
        except Exception as e:
            logger.warning(f"chat stream error: {e}")
            fallback = "Sorry — the AI hit an error. Try again in a moment."
            await self.append(user.id, "assistant", fallback)
            yield fallback


# Accumulate streamed tokens into a single assistant message at the end of the stream.
async def _accumulate(svc: "ChatService", user: User, token: str) -> None:
    key = f"chat-buf:{user.id}"
    try:
        await svc.redis.append(key, token)
        await svc.redis.expire(key, 120)
    except Exception:
        pass


async def _finalize_buffer(svc: "ChatService", user: User) -> None:
    key = f"chat-buf:{user.id}"
    buf = await svc.redis.get(key)
    if buf:
        await svc.append(user.id, "assistant", buf)
        await svc.redis.delete(key)


async def _stream_anthropic(llm, system: str, prior: list[dict]) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": llm.model, "max_tokens": 600, "stream": True,
            "system": system,
            "messages": [m for m in prior if m["role"] in ("user", "assistant")],
        }
        async with client.stream(
            "POST", f"{llm.base_url}/v1/messages",
            headers={"x-api-key": llm.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json=payload,
        ) as r:
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    evt = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if evt.get("type") == "content_block_delta":
                    delta = evt.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")


async def _stream_openai_compatible(llm, messages: list[dict]) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {"model": llm.model, "max_tokens": 600, "temperature": 0.4, "stream": True, "messages": messages}
        async with client.stream(
            "POST", f"{llm.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {llm.api_key}", "Content-Type": "application/json"},
            json=payload,
        ) as r:
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    evt = json.loads(data)
                except json.JSONDecodeError:
                    continue
                for choice in evt.get("choices", []):
                    delta = choice.get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
