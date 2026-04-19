"""Services powering the 5 unique features + AI layers."""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from core.llm import get_llm
from models.content import Content
from models.user import User


VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


def _vibe_dict(content: Content) -> dict[str, float]:
    return {d: float(getattr(content, f"vibe_{d}")) for d in VIBE_DIMS}


def _dna_dict(user: User) -> dict[str, float]:
    return {d: float(getattr(user, f"dna_{d}")) for d in VIBE_DIMS}


def _dna_match(user_dna: dict[str, float], vibe: dict[str, float]) -> float:
    """Lower L2 distance = higher match."""
    dist = sum((user_dna[d] - vibe[d]) ** 2 for d in VIBE_DIMS) ** 0.5
    return max(0.0, 1.0 - dist / (len(VIBE_DIMS) ** 0.5))


class UniqueService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def taste_dna(self, user_id: uuid.UUID) -> dict[str, Any]:
        user = await self.get_user(user_id)
        if user is None:
            return {"dna": {d: 0.5 for d in VIBE_DIMS}, "samples": 0}
        return {"dna": _dna_dict(user), "samples": user.dna_samples}

    async def mood_recommendations(
        self, user_id: uuid.UUID, chill_tense: float, light_thoughtful: float, limit: int
    ) -> list[dict]:
        user = await self.get_user(user_id)
        user_dna = _dna_dict(user) if user else {d: 0.5 for d in VIBE_DIMS}

        # Pull a pool, then score by mood distance + DNA match.
        res = await self.session.execute(
            select(Content).where(Content.is_active == True).order_by(Content.popularity_score.desc()).limit(limit * 10)
        )
        items = list(res.scalars().all())
        scored = []
        for c in items:
            md = ((c.mood_chill_tense - chill_tense) ** 2 + (c.mood_light_thoughtful - light_thoughtful) ** 2) ** 0.5
            mood_score = max(0.0, 1.0 - md / 1.4142)
            dna_score = _dna_match(user_dna, _vibe_dict(c))
            blended = 0.7 * mood_score + 0.3 * dna_score
            scored.append((c, blended, mood_score, dna_score))
        scored.sort(key=lambda t: t[1], reverse=True)
        return [
            {
                "content": c, "score": s, "mood_score": ms, "dna_score": ds,
            }
            for c, s, ms, ds in scored[:limit]
        ]

    async def time_budget_recommendations(
        self, user_id: uuid.UUID, minutes: int, limit: int, tolerance_pct: int
    ) -> list[dict]:
        user = await self.get_user(user_id)
        user_dna = _dna_dict(user) if user else {d: 0.5 for d in VIBE_DIMS}
        target_secs = minutes * 60
        tol = target_secs * (tolerance_pct / 100.0)

        res = await self.session.execute(
            select(Content).where(
                Content.is_active == True,
                Content.duration_seconds.isnot(None),
                Content.duration_seconds.between(int(target_secs - tol), int(target_secs + tol)),
            ).order_by(Content.popularity_score.desc()).limit(limit * 8)
        )
        items = list(res.scalars().all())
        scored = []
        for c in items:
            length_fit = 1.0 - abs((c.duration_seconds or target_secs) - target_secs) / max(tol, 1)
            dna = _dna_match(user_dna, _vibe_dict(c))
            blended = 0.45 * float(c.completion_rate) + 0.35 * dna + 0.2 * length_fit
            scored.append({"content": c, "score": blended, "length_fit": length_fit, "completion_rate": float(c.completion_rate), "dna_score": dna})
        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:limit]

    async def explain(self, user_id: uuid.UUID, content_id: uuid.UUID) -> dict[str, Any] | None:
        content = (await self.session.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        user = await self.get_user(user_id)
        if content is None:
            return None
        user_dna = _dna_dict(user) if user else {d: 0.5 for d in VIBE_DIMS}
        vibe = _vibe_dict(content)

        # Build human-readable signals (0..1)
        signals = []

        # Per-dim DNA match — pick the two best dims
        dim_matches = [(d, 1 - abs(user_dna[d] - vibe[d])) for d in VIBE_DIMS]
        dim_matches.sort(key=lambda t: t[1], reverse=True)
        for d, v in dim_matches[:2]:
            signals.append({
                "name": f"{d}_match",
                "value": round(float(v), 3),
                "description": f"Your {d} affinity ({round(user_dna[d] * 100)}%) matches this title's {d} ({round(vibe[d] * 100)}%)",
            })

        signals.append({
            "name": "popularity",
            "value": round(float(min(1.0, content.popularity_score)), 3),
            "description": f"Popularity signal among all viewers",
        })
        signals.append({
            "name": "completion_rate",
            "value": round(float(content.completion_rate), 3),
            "description": "Fraction of viewers who finished this title",
        })
        signals.sort(key=lambda s: s["value"], reverse=True)

        dominant = signals[0]["description"] if signals else "Recommended for you"

        ai_summary = await self._ai_why(user, content, signals)
        return {
            "content_id": content.id,
            "signals": signals,
            "dominant_reason": dominant,
            "ai_summary": ai_summary,
        }

    async def _ai_why(self, user: User | None, content: Content, signals: list[dict]) -> str | None:
        llm = get_llm()
        if not llm.enabled:
            return None
        prompt = (
            f"Content: '{content.title}' ({content.type}, {content.release_year}).\n"
            f"Description: {content.description[:280] if content.description else ''}\n"
            f"Vibe (0-1): {_vibe_dict(content)}\n"
            f"Viewer taste DNA (0-1): {_dna_dict(user) if user else 'unknown'}\n"
            f"Top signals: {[s['name'] + '=' + str(s['value']) for s in signals[:3]]}\n\n"
            f"Write ONE sentence explaining why THIS specific viewer should watch THIS title, "
            f"referencing their taste profile in natural language (no numbers). Max 28 words."
        )
        out = await llm.complete(
            system="You are a concise, personal movie recommender.",
            user=prompt,
            max_tokens=120,
            temperature=0.5,
        )
        return (out or "").strip() if out else None

    async def co_viewer(self, user_ids: list[uuid.UUID], limit: int) -> list[dict]:
        users = []
        for uid in user_ids:
            u = await self.get_user(uid)
            if u:
                users.append(u)
        if not users:
            return []
        blended = {d: sum(getattr(u, f"dna_{d}") for u in users) / len(users) for d in VIBE_DIMS}
        res = await self.session.execute(
            select(Content).where(Content.is_active == True).order_by(Content.popularity_score.desc()).limit(limit * 10)
        )
        items = list(res.scalars().all())
        scored = []
        for c in items:
            v = _vibe_dict(c)
            dna_score = _dna_match(blended, v)
            # Tolerance zone: min(user_dist) measures "worst-case disappointment"
            worst = max(_dna_match(_dna_dict(u), v) for u in users) - min(_dna_match(_dna_dict(u), v) for u in users)
            stretch = 1.0 - min(1.0, worst * 1.5)  # smaller spread = safer pick
            blended_score = 0.65 * dna_score + 0.35 * stretch
            scored.append({"content": c, "score": blended_score, "dna_match": dna_score, "agreement": stretch})
        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:limit]

    async def record_feedback(
        self, user_id: uuid.UUID, content_id: uuid.UUID, surface: str, feedback: int, reason: str | None
    ) -> None:
        await self.session.execute(sql_text("""
            INSERT INTO rec_feedback (user_id, content_id, surface, feedback, reason, created_at)
            VALUES (:uid, :cid, :s, :f, :r, :ts)
        """), {
            "uid": str(user_id), "cid": str(content_id), "s": surface,
            "f": feedback, "r": reason, "ts": datetime.now(timezone.utc),
        })
        await self.session.commit()

    async def nl_search(self, user_id: uuid.UUID, query: str, limit: int) -> dict[str, Any]:
        llm = get_llm()
        parsed: dict = {}
        if llm.enabled:
            parsed = await llm.complete_json(
                system=(
                    "You extract structured filters from natural-language queries about movies and series. "
                    "Return JSON with any of: genres (array of strings like 'Action','Sci-Fi'), decade (int like 1990), "
                    "max_minutes (int), min_year (int), max_year (int), mood (one of 'chill','tense','light','thoughtful'), "
                    "keywords (array of strings). Omit keys you cannot infer confidently."
                ),
                user=f"Query: {query}",
                max_tokens=200,
                temperature=0.0,
            ) or {}

        stmt = select(Content).where(Content.is_active == True)
        if isinstance(parsed.get("min_year"), int):
            stmt = stmt.where(Content.release_year >= parsed["min_year"])
        if isinstance(parsed.get("max_year"), int):
            stmt = stmt.where(Content.release_year <= parsed["max_year"])
        if isinstance(parsed.get("decade"), int):
            d = parsed["decade"]
            stmt = stmt.where(Content.release_year >= d, Content.release_year < d + 10)
        if isinstance(parsed.get("max_minutes"), int):
            stmt = stmt.where(Content.duration_seconds <= parsed["max_minutes"] * 60)

        mood_map = {
            "chill": (0.25, 0.3), "tense": (0.8, 0.4),
            "light": (0.3, 0.2), "thoughtful": (0.4, 0.85),
        }
        kw = parsed.get("keywords") or []
        if kw:
            from sqlalchemy import or_, func as sa_func
            clauses = [sa_func.lower(Content.title).like(f"%{k.lower()}%") for k in kw]
            clauses += [sa_func.lower(Content.description).like(f"%{k.lower()}%") for k in kw if k]
            if clauses:
                stmt = stmt.where(or_(*clauses))
        stmt = stmt.order_by(Content.popularity_score.desc()).limit(limit * 6)
        items = list((await self.session.execute(stmt)).scalars().all())

        mood = parsed.get("mood")
        if mood in mood_map and items:
            ct, lt = mood_map[mood]
            items.sort(key=lambda c: ((c.mood_chill_tense - ct) ** 2 + (c.mood_light_thoughtful - lt) ** 2))
        items = items[:limit]
        return {"parsed_filters": parsed, "items": items}

    async def anti_recs(self, user_id: uuid.UUID, limit: int) -> list[dict]:
        user = await self.get_user(user_id)
        user_dna = _dna_dict(user) if user else {d: 0.5 for d in VIBE_DIMS}
        res = await self.session.execute(
            select(Content).where(Content.is_active == True).order_by(Content.popularity_score.desc()).limit(200)
        )
        items = list(res.scalars().all())
        scored = []
        for c in items:
            dna = _dna_match(user_dna, _vibe_dict(c))
            scored.append((c, 1.0 - dna))
        scored.sort(key=lambda t: t[1], reverse=True)
        return [{"content": c, "anti_score": s} for c, s in scored[:limit]]

    async def spoiler_free_description(self, content_id: uuid.UUID) -> dict[str, Any] | None:
        content = (await self.session.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if content is None:
            return None
        llm = get_llm()
        rewritten = None
        if llm.enabled and content.description:
            rewritten = await llm.complete(
                system=(
                    "You rewrite movie/TV descriptions to be SPOILER-FREE. "
                    "Preserve genre, tone, mood. Remove plot twists, character fates, ending hints, "
                    "and any specific event past the first 20% of the story. Keep it 2-3 sentences. Tease; do not reveal."
                ),
                user=f"Title: {content.title}\n\nOriginal: {content.description}",
                max_tokens=200,
                temperature=0.4,
            )
        return {
            "content_id": content.id,
            "original": content.description,
            "spoiler_free": (rewritten or content.description or "").strip(),
            "ai_used": bool(rewritten),
        }

    async def raw_browse(self, sort: str, limit: int, offset: int) -> list[Content]:
        from sqlalchemy import asc, desc as sql_desc
        stmt = select(Content).where(Content.is_active == True)
        if sort == "popular":
            stmt = stmt.order_by(sql_desc(Content.popularity_score))
        elif sort == "year_desc":
            stmt = stmt.order_by(sql_desc(Content.release_year))
        elif sort == "year_asc":
            stmt = stmt.order_by(asc(Content.release_year))
        elif sort == "title":
            stmt = stmt.order_by(asc(Content.title))
        else:
            stmt = stmt.order_by(sql_desc(Content.popularity_score))
        stmt = stmt.limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def ai_rerank(self, user: User | None, candidates: list[Content], limit: int) -> list[Content]:
        llm = get_llm()
        if not llm.enabled or not candidates:
            return candidates[:limit]
        user_dna = _dna_dict(user) if user else None
        items = [
            {
                "id": str(c.id),
                "title": c.title,
                "year": c.release_year,
                "genres": c.genre_ids,
                "vibe": _vibe_dict(c),
            }
            for c in candidates[:40]
        ]
        payload = {
            "viewer_taste_dna": user_dna,
            "viewer_samples": getattr(user, "dna_samples", 0) if user else 0,
            "candidates": items,
            "return_top_n": min(limit, len(items)),
        }
        import json
        parsed = await llm.complete_json(
            system=(
                "You are an expert recommendation reranker. Given a viewer's taste DNA (0..1 on 6 dimensions: "
                "pace, emotion, darkness, humor, complexity, spectacle) and a set of candidate titles with their vibe "
                "vectors, produce the best ordering for THIS viewer. Return JSON: {\"ranked_ids\": [\"id1\", \"id2\", ...]}."
            ),
            user=json.dumps(payload),
            max_tokens=600,
            temperature=0.2,
        )
        if not parsed or "ranked_ids" not in parsed:
            return candidates[:limit]
        id_to_c = {str(c.id): c for c in candidates}
        reordered = []
        seen = set()
        for cid in parsed["ranked_ids"]:
            if cid in id_to_c and cid not in seen:
                reordered.append(id_to_c[cid])
                seen.add(cid)
        for c in candidates:
            if str(c.id) not in seen:
                reordered.append(c)
        return reordered[:limit]
