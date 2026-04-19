"""Chat-80: facts, threads, anti-goals, personas, self-analysis, decisive, export, share."""
import json
import secrets
import uuid
from datetime import datetime, date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm import get_llm
from middleware.auth_middleware import get_current_user
from models.user import User

router = APIRouter(prefix="/chat", tags=["chat_v2"])


# ─── Long-term facts (memorable user preferences) ─────────
class FactIn(BaseModel):
    fact: str = Field(min_length=3, max_length=500)


@router.post("/facts")
async def add_fact(
    body: FactIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO user_facts (user_id, fact) VALUES (:u, :f)
    """), {"u": str(user.id), "f": body.fact})
    await db.commit()
    return {"status": "ok"}


@router.get("/facts")
async def list_facts(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, fact, source, confidence, created_at FROM user_facts
        WHERE user_id=:u ORDER BY created_at DESC LIMIT 50
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "created_at": r["created_at"].isoformat()} for r in rows]}


@router.delete("/facts/{fact_id}")
async def delete_fact(
    fact_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("DELETE FROM user_facts WHERE id=:i AND user_id=:u"),
                     {"i": fact_id, "u": str(user.id)})
    await db.commit()
    return {"status": "ok"}


# ─── Anti-goals ───────────────────────────────────────────
class AntiGoalIn(BaseModel):
    avoid_genres: list[int] = Field(default_factory=list)
    avoid_keywords: list[str] = Field(default_factory=list)
    avoid_cast_names: list[str] = Field(default_factory=list)
    max_dnl_darkness: float | None = Field(default=None, ge=0, le=1)


@router.put("/anti-goals")
async def set_anti_goals(
    body: AntiGoalIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO anti_goals (user_id, avoid_genres, avoid_keywords, avoid_cast_names, max_dnl_darkness)
        VALUES (:u, :g, :k, :c, :d)
        ON CONFLICT (user_id) DO UPDATE SET
            avoid_genres=:g, avoid_keywords=:k, avoid_cast_names=:c, max_dnl_darkness=:d,
            updated_at=now()
    """), {"u": str(user.id), "g": body.avoid_genres, "k": body.avoid_keywords,
           "c": body.avoid_cast_names, "d": body.max_dnl_darkness})
    await db.commit()
    return {"status": "ok"}


@router.get("/anti-goals")
async def get_anti_goals(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("SELECT * FROM anti_goals WHERE user_id=:u"),
                            {"u": str(user.id)})).mappings().first()
    if not row:
        return {"avoid_genres": [], "avoid_keywords": [], "avoid_cast_names": [], "max_dnl_darkness": None}
    return dict(row) | {"user_id": str(row["user_id"]), "updated_at": row["updated_at"].isoformat()}


# ─── Threads (multiple conversations) ─────────────────────
class ThreadCreate(BaseModel):
    title: str = Field(default="New chat", max_length=200)
    persona: str = Field(default="friendly", pattern="^(friendly|critic|expert|concise|formal)$")


@router.post("/threads")
async def create_thread(
    body: ThreadCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(text("""
        INSERT INTO chat_threads (user_id, title, persona) VALUES (:u, :t, :p) RETURNING id
    """), {"u": str(user.id), "t": body.title, "p": body.persona})
    await db.commit()
    return {"id": str(r.scalar_one())}


@router.get("/threads")
async def list_threads(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, title, persona, pinned, share_token, created_at, updated_at
        FROM chat_threads WHERE user_id=:u ORDER BY pinned DESC, updated_at DESC LIMIT 40
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"]),
                       "created_at": r["created_at"].isoformat(),
                       "updated_at": r["updated_at"].isoformat()} for r in rows]}


@router.post("/threads/{thread_id}/share")
async def share_thread(
    thread_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tok = secrets.token_urlsafe(10)
    r = await db.execute(text("""
        UPDATE chat_threads SET share_token=:t WHERE id=:i AND user_id=:u
        RETURNING id
    """), {"t": tok, "i": str(thread_id), "u": str(user.id)})
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404)
    await db.commit()
    return {"share_token": tok, "share_url": f"/chat/shared/{tok}"}


# ─── Token usage meter ────────────────────────────────────
@router.get("/usage")
async def usage(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    month = date.today().strftime("%Y-%m")
    row = (await db.execute(text("""
        SELECT tokens_used, calls FROM llm_usage WHERE user_id=:u AND month=:m
    """), {"u": str(user.id), "m": month})).first()
    used = int(row[0]) if row else 0
    calls = int(row[1]) if row else 0
    quota = 100_000
    return {"month": month, "tokens_used": used, "calls": calls, "quota": quota,
            "pct_used": round(used / quota, 3)}


# ─── Self-analysis: RO describes your taste ───────────────
@router.post("/self-analysis")
async def self_analysis(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    llm = get_llm()
    if not llm.enabled:
        return {"summary": "LLM not configured"}
    dims = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")
    dna = {d: round(float(getattr(user, f"dna_{d}")), 2) for d in dims}
    recent = (await db.execute(text("""
        SELECT c.title FROM watch_history w JOIN content c ON c.id=w.content_id
        WHERE w.user_id=:u AND w.completed = true ORDER BY w.last_watched_at DESC LIMIT 10
    """), {"u": str(user.id)})).scalars().all()
    prompt = (
        f"Taste DNA: {dna}\n"
        f"Recently finished: {', '.join(recent[:10])}\n\n"
        "In exactly 3 short paragraphs, describe this viewer's taste like a sharp-tongued film critic "
        "would describe a friend. Avoid numbers. Be specific, a little teasing."
    )
    out = await llm.complete(
        system="You are RO — warm, perceptive, opinionated.",
        user=prompt, max_tokens=400, temperature=0.6,
    )
    return {"summary": out or "Not enough data yet."}


# ─── Decisive mode: force a single pick ───────────────────
class DecisiveIn(BaseModel):
    context: str = Field(default="", max_length=200)


@router.post("/decisive")
async def decisive(
    body: DecisiveIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Call the ML rec with limit=1, skip if user has seen
    rows = (await db.execute(text("""
        SELECT c.id, c.title, c.release_year, c.thumbnail_url, c.description
        FROM content c
        WHERE c.is_active = true
          AND NOT EXISTS (SELECT 1 FROM watch_history w WHERE w.user_id=:u AND w.content_id=c.id)
        ORDER BY c.popularity_score DESC LIMIT 1
    """), {"u": str(user.id)})).mappings().first()
    if not rows:
        raise HTTPException(status_code=404, detail="no catalog")
    llm = get_llm()
    reason = f"Because your top unwatched popular pick right now is {rows['title']}."
    if llm.enabled:
        r = await llm.complete(
            system="You are RO in 'decisive mode'. One sentence, imperative voice, no hedging.",
            user=f"Pick: {rows['title']} ({rows['release_year']}). Context: {body.context}. Tell them to watch it.",
            max_tokens=60, temperature=0.6,
        )
        reason = r or reason
    return {"id": str(rows["id"]), "title": rows["title"], "thumbnail_url": rows["thumbnail_url"],
            "verdict": reason}


# ─── Export a full conversation as JSON ───────────────────
@router.get("/export")
async def export_chat(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from core.redis import get_redis
    redis = await get_redis()
    raw = await redis.get(f"chat:{user.id}") or "[]"
    facts = (await db.execute(text("SELECT fact FROM user_facts WHERE user_id=:u"),
                              {"u": str(user.id)})).scalars().all()
    feedback = (await db.execute(text("""
        SELECT turn_index, user_message, assistant_message, feedback, created_at
        FROM chat_feedback WHERE user_id=:u ORDER BY created_at DESC LIMIT 100
    """), {"u": str(user.id)})).mappings().all()
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "user_id": str(user.id),
        "current_session": json.loads(raw),
        "remembered_facts": list(facts),
        "recent_feedback": [
            {**r, "created_at": r["created_at"].isoformat()} for r in feedback
        ],
    }


# ─── Citation mode — ranker signals for a title ──────────
@router.get("/cite/{content_id}")
async def cite(
    content_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        SELECT c.title, c.popularity_score, c.completion_rate, c.vibe_pace, c.vibe_emotion,
               c.vibe_darkness, c.vibe_humor, c.vibe_complexity, c.vibe_spectacle
        FROM content c WHERE c.id=:c
    """), {"c": str(content_id)})).mappings().first()
    if not row:
        raise HTTPException(status_code=404)
    dims = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")
    dna = [float(getattr(user, f"dna_{d}")) for d in dims]
    vibe = [float(row[f"vibe_{d}"]) for d in dims]
    dist = sum((a - b) ** 2 for a, b in zip(dna, vibe)) ** 0.5
    dna_match = max(0.0, 1.0 - dist / (len(dims) ** 0.5))
    confidence = "high" if dna_match > 0.85 else "medium" if dna_match > 0.6 else "low"
    return {
        "title": row["title"],
        "signals": {
            "dna_match": round(dna_match, 3),
            "popularity": round(float(row["popularity_score"] or 0), 3),
            "completion_rate": round(float(row["completion_rate"] or 0), 3),
        },
        "confidence": confidence,
        "explanation": f"DNA alignment {round(dna_match*100)}%, popularity {round(float(row['popularity_score'] or 0)*100)}%, finish rate {round(float(row['completion_rate'] or 0)*100)}%",
    }


# ─── Plugins (webhook-registered external agents) ─────────
class PluginIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    webhook_url: str = Field(max_length=500)
    trigger_keywords: list[str] = Field(min_length=1, max_length=10)


@router.post("/plugins")
async def register_plugin(
    body: PluginIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO chat_plugins (user_id, name, webhook_url, trigger_keywords)
        VALUES (:u, :n, :w, :k)
    """), {"u": str(user.id), "n": body.name, "w": body.webhook_url, "k": body.trigger_keywords})
    await db.commit()
    return {"status": "ok"}


@router.get("/plugins")
async def list_plugins(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, name, webhook_url, trigger_keywords, is_active FROM chat_plugins WHERE user_id=:u
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"])} for r in rows]}


# ─── Weekly digest (LLM-written) ──────────────────────────
@router.post("/digest/weekly")
async def weekly_digest(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT c.title, w.watch_pct, w.completed, w.last_watched_at
        FROM watch_history w JOIN content c ON c.id=w.content_id
        WHERE w.user_id=:u AND w.last_watched_at > now() - interval '7 days'
        ORDER BY w.last_watched_at DESC
    """), {"u": str(user.id)})).mappings().all()
    if not rows:
        return {"digest": "Nothing watched this week. Pick something tonight?"}
    llm = get_llm()
    if not llm.enabled:
        titles = ", ".join([r["title"] for r in rows[:5]])
        return {"digest": f"This week you watched: {titles}"}
    summary = [{"title": r["title"], "pct": round(float(r["watch_pct"]), 2),
                "completed": bool(r["completed"])} for r in rows[:10]]
    out = await llm.complete(
        system="You are RO writing a weekly movie/TV digest. 3 paragraphs, personal, observations not numbers.",
        user=f"This week's viewing: {json.dumps(summary)}",
        max_tokens=400, temperature=0.6,
    )
    return {"digest": out or "Great week of watching."}


# ─── Taste time-machine ───────────────────────────────────
@router.get("/time-machine/{year}")
async def time_machine(
    year: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, title, release_year, thumbnail_url, popularity_score
        FROM content
        WHERE is_active = true AND release_year = :y
        ORDER BY popularity_score DESC LIMIT 12
    """), {"y": year})).mappings().all()
    return {"year": year, "items": [{**r, "id": str(r["id"])} for r in rows]}
