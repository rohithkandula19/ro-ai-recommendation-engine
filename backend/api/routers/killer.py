"""RO Wrapped + Blind Date + Mixer + Skill Tree + Genre Learning."""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User

router = APIRouter(tags=["killer"])
VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


# ─── RO Wrapped ───────────────────────────────────────────
@router.get("/wrapped/{year}")
async def wrapped(
    year: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT c.title, c.release_year, c.thumbnail_url, c.genre_ids, w.watch_pct, w.last_watched_at
        FROM watch_history w JOIN content c ON c.id=w.content_id
        WHERE w.user_id=:u AND EXTRACT(YEAR FROM w.last_watched_at) = :y
        ORDER BY w.last_watched_at ASC
    """), {"u": str(user.id), "y": year})).mappings().all()
    total = len(rows)
    completed = sum(1 for r in rows if r["watch_pct"] >= 0.9)
    genre_counts: dict[int, int] = {}
    for r in rows:
        for g in r["genre_ids"] or []:
            genre_counts[g] = genre_counts.get(g, 0) + 1
    top_genre_id = max(genre_counts, key=genre_counts.get) if genre_counts else None
    top_genre = None
    if top_genre_id:
        tg = (await db.execute(text("SELECT name FROM genres WHERE id=:i"), {"i": top_genre_id})).scalar_one_or_none()
        top_genre = tg
    first_watch = rows[0]["title"] if rows else None
    last_watch = rows[-1]["title"] if rows else None
    dna = {d: round(float(getattr(user, f"dna_{d}")), 2) for d in VIBE_DIMS}
    top_axis = max(dna, key=dna.get)
    return {
        "year": year,
        "total_watched": total,
        "completed": completed,
        "top_genre": top_genre,
        "first_watch": first_watch,
        "last_watch": last_watch,
        "dna": dna,
        "top_axis": top_axis,
        "spotlight": [{"title": r["title"], "thumbnail_url": r["thumbnail_url"], "year": r["release_year"]} for r in rows[:6]],
    }


# ─── Blind Date ───────────────────────────────────────────
@router.post("/blind-date/start")
async def blind_date_start(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        SELECT c.id FROM content c
        WHERE c.is_active=true
          AND NOT EXISTS (SELECT 1 FROM watch_history w WHERE w.user_id=:u AND w.content_id=c.id)
          AND NOT EXISTS (SELECT 1 FROM blind_dates b WHERE b.user_id=:u AND b.content_id=c.id)
        ORDER BY random() LIMIT 1
    """), {"u": str(user.id)})).first()
    if not row:
        raise HTTPException(status_code=404, detail="no pick")
    cid = row[0]
    r = await db.execute(text("""
        INSERT INTO blind_dates (user_id, content_id) VALUES (:u, :c) RETURNING id
    """), {"u": str(user.id), "c": str(cid)})
    await db.commit()
    return {"blind_date_id": str(r.scalar_one()),
            "hint": "Trust us. Watch this. Come back to reveal."}


@router.post("/blind-date/{bd_id}/reveal")
async def blind_date_reveal(
    bd_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("""
        UPDATE blind_dates SET revealed=true WHERE id=:i AND user_id=:u
        RETURNING content_id
    """), {"i": str(bd_id), "u": str(user.id)})).first()
    if not row:
        raise HTTPException(status_code=404)
    await db.commit()
    content = (await db.execute(text("""
        SELECT id, title, release_year, thumbnail_url, description FROM content WHERE id=:c
    """), {"c": str(row[0])})).mappings().first()
    return dict(content) | {"id": str(content["id"])}


class BDRateIn(BaseModel):
    rating: int = Field(ge=1, le=5)


@router.post("/blind-date/{bd_id}/rate")
async def blind_date_rate(
    bd_id: uuid.UUID, body: BDRateIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("UPDATE blind_dates SET rating=:r WHERE id=:i AND user_id=:u"),
                     {"r": body.rating, "i": str(bd_id), "u": str(user.id)})
    await db.commit()
    return {"status": "ok"}


# ─── RO Mixer ─────────────────────────────────────────────
class MixerIn(BaseModel):
    other_user_id: uuid.UUID
    limit: int = Field(default=12, ge=1, le=30)


@router.post("/mixer")
async def mixer(
    body: MixerIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    other = (await db.execute(text("""
        SELECT id, display_name, dna_pace, dna_emotion, dna_darkness, dna_humor, dna_complexity, dna_spectacle
        FROM users WHERE id=:u
    """), {"u": str(body.other_user_id)})).mappings().first()
    if not other:
        raise HTTPException(status_code=404, detail="user not found")
    blended = {d: (float(getattr(user, f"dna_{d}")) + float(other[f"dna_{d}"])) / 2 for d in VIBE_DIMS}
    dist_expr = " + ".join([f"power(c.vibe_{d} - :d{i}, 2)" for i, d in enumerate(VIBE_DIMS)])
    params = {f"d{i}": blended[d] for i, d in enumerate(VIBE_DIMS)}
    params["u1"] = str(user.id); params["u2"] = str(body.other_user_id); params["lim"] = body.limit
    rows = (await db.execute(text(f"""
        SELECT c.id, c.title, c.thumbnail_url, c.release_year, sqrt({dist_expr}) AS dist
        FROM content c
        WHERE c.is_active=true
          AND NOT EXISTS (SELECT 1 FROM watch_history w WHERE w.user_id=:u1 AND w.content_id=c.id)
          AND NOT EXISTS (SELECT 1 FROM watch_history w WHERE w.user_id=:u2 AND w.content_id=c.id)
        ORDER BY dist ASC LIMIT :lim
    """), params)).mappings().all()
    return {
        "other": {"id": str(other["id"]), "display_name": other["display_name"]},
        "blended_dna": blended,
        "items": [{"id": str(r["id"]), "title": r["title"],
                   "thumbnail_url": r["thumbnail_url"],
                   "release_year": r["release_year"],
                   "match": round(1 - min(float(r["dist"]) / 2.449, 1), 3)} for r in rows],
    }


# ─── Skill tree / achievements ────────────────────────────
ACHIEVEMENTS = [
    {"key": "first_rating", "label": "First rating", "emoji": "⭐", "desc": "Rate any title"},
    {"key": "watched_10", "label": "Casual", "emoji": "🎬", "desc": "Watch 10 titles"},
    {"key": "watched_50", "label": "Enthusiast", "emoji": "🎥", "desc": "Watch 50 titles"},
    {"key": "watched_100", "label": "Veteran", "emoji": "🏆", "desc": "Watch 100 titles"},
    {"key": "three_genres", "label": "Curious", "emoji": "🧭", "desc": "Watch 3 different genres"},
    {"key": "review_written", "label": "Critic", "emoji": "✍️", "desc": "Write your first review"},
    {"key": "blind_date", "label": "Risk Taker", "emoji": "🎲", "desc": "Complete a Blind Date"},
    {"key": "streak_7", "label": "Week Streak", "emoji": "🔥", "desc": "7-day watch streak"},
    {"key": "mixer_pick", "label": "Perfect Pairing", "emoji": "💞", "desc": "Watch a Mixer pick with a friend"},
    {"key": "friend_5", "label": "Social", "emoji": "👥", "desc": "Follow 5 users"},
]


@router.get("/achievements")
async def achievements(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    unlocked = {r[0] for r in (await db.execute(text(
        "SELECT key FROM achievements WHERE user_id=:u"
    ), {"u": str(user.id)})).all()}
    # Auto-check common ones against live data
    counts = (await db.execute(text("""
        SELECT
          (SELECT COUNT(*) FROM ratings WHERE user_id=:u) AS ratings_n,
          (SELECT COUNT(*) FROM watch_history WHERE user_id=:u AND completed=true) AS watched_n,
          (SELECT COUNT(DISTINCT g) FROM watch_history w
             JOIN content c ON c.id=w.content_id, LATERAL unnest(c.genre_ids) g
             WHERE w.user_id=:u) AS distinct_genres,
          (SELECT COUNT(*) FROM reviews WHERE user_id=:u) AS reviews_n,
          (SELECT COUNT(*) FROM blind_dates WHERE user_id=:u AND rating IS NOT NULL) AS blind_n,
          (SELECT COUNT(*) FROM friendships WHERE user_id=:u AND status='accepted') AS friends_n,
          (SELECT best_days FROM user_streaks WHERE user_id=:u) AS best_streak
    """), {"u": str(user.id)})).mappings().first()
    checks = {
        "first_rating": counts["ratings_n"] and counts["ratings_n"] >= 1,
        "watched_10": counts["watched_n"] and counts["watched_n"] >= 10,
        "watched_50": counts["watched_n"] and counts["watched_n"] >= 50,
        "watched_100": counts["watched_n"] and counts["watched_n"] >= 100,
        "three_genres": counts["distinct_genres"] and counts["distinct_genres"] >= 3,
        "review_written": counts["reviews_n"] and counts["reviews_n"] >= 1,
        "blind_date": counts["blind_n"] and counts["blind_n"] >= 1,
        "streak_7": counts["best_streak"] and counts["best_streak"] >= 7,
        "friend_5": counts["friends_n"] and counts["friends_n"] >= 5,
    }
    for k, ok in checks.items():
        if ok and k not in unlocked:
            await db.execute(text("""
                INSERT INTO achievements (user_id, key) VALUES (:u, :k) ON CONFLICT DO NOTHING
            """), {"u": str(user.id), "k": k})
            unlocked.add(k)
    await db.commit()
    return {
        "items": [{**a, "unlocked": a["key"] in unlocked} for a in ACHIEVEMENTS],
        "progress": f"{len(unlocked)}/{len(ACHIEVEMENTS)}",
    }


# ─── Genre Learning (5-title ramp) ────────────────────────
@router.get("/genre-learning/{genre_id}")
async def genre_learning(
    genre_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Pull 5 titles in this genre sorted by *closeness to user DNA* ASCENDING
    # so the first pick is most aligned, gradually getting farther (gentler ramp).
    user_dna = [float(getattr(user, f"dna_{d}")) for d in VIBE_DIMS]
    dist_expr = " + ".join([f"power(c.vibe_{d} - :d{i}, 2)" for i, d in enumerate(VIBE_DIMS)])
    params = {f"d{i}": user_dna[i] for i in range(len(VIBE_DIMS))}
    params["g"] = genre_id
    rows = (await db.execute(text(f"""
        SELECT c.id, c.title, c.thumbnail_url, c.release_year, sqrt({dist_expr}) AS dist
        FROM content c
        WHERE c.is_active=true AND :g = ANY(c.genre_ids)
        ORDER BY dist ASC LIMIT 5
    """), params)).mappings().all()
    genre_name = (await db.execute(text("SELECT name FROM genres WHERE id=:i"),
                                   {"i": genre_id})).scalar_one_or_none()
    return {
        "genre": genre_name,
        "ramp": [{"id": str(r["id"]), "title": r["title"],
                  "thumbnail_url": r["thumbnail_url"], "release_year": r["release_year"],
                  "step": idx + 1, "difficulty": round(float(r["dist"]), 2)}
                 for idx, r in enumerate(rows)],
    }
