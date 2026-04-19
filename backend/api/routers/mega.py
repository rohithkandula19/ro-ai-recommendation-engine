"""All Batch B endpoints in one router.

Grouped by feature:
  semantic search, AI collections, auto-tag, voice (no server-side — frontend only),
  friends, taste-twins, shared watchlists, reviews + comments, multi-profiles,
  episodes, cast/persons, parental (in profiles), watch-party, notifications,
  A/B experiments, cohort retention, data export, billing stubs.
"""
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm import get_llm
from middleware.auth_middleware import get_current_user, require_admin
from models.content import Content
from models.user import User


router = APIRouter(tags=["mega"])

VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


# ─────────────────────────────────────────────────────────
# 1. SEMANTIC SEARCH — delegates to ml_service FAISS index
# ─────────────────────────────────────────────────────────
class SemanticSearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=50)


@router.post("/search/semantic")
async def semantic_search(
    body: SemanticSearchIn,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Ask ml_service for a content_id list via FAISS similar-by-text.
    from core.config import settings
    ids = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{settings.ML_SERVICE_URL}/ml/semantic-search",
                                  json={"query": body.query, "k": body.limit})
            if r.status_code == 200:
                ids = [uuid.UUID(x) for x in r.json().get("ids", [])]
    except Exception:
        pass

    if ids:
        res = await db.execute(select(Content).where(Content.id.in_(ids)))
        items = {str(c.id): c for c in res.scalars().all()}
        ordered = [items[str(i)] for i in ids if str(i) in items]
    else:
        # fallback: ILIKE
        q = f"%{body.query.lower()}%"
        res = await db.execute(
            select(Content).where(
                Content.is_active == True,
                func.lower(Content.description).like(q),
            ).limit(body.limit)
        )
        ordered = list(res.scalars().all())

    return {
        "query": body.query,
        "results": [{"id": str(c.id), "title": c.title, "release_year": c.release_year,
                     "thumbnail_url": c.thumbnail_url, "type": c.type} for c in ordered],
    }


# ─────────────────────────────────────────────────────────
# 2. AI COLLECTION GENERATOR
# ─────────────────────────────────────────────────────────
class AICollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=3, max_length=500)
    is_public: bool = False


@router.post("/ai-collections")
async def create_ai_collection(
    body: AICollectionIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    llm = get_llm()
    # pull 60 candidates ordered by popularity
    cands = (await db.execute(text("""
        SELECT id, title, release_year, type, description
        FROM content WHERE is_active = true
        ORDER BY popularity_score DESC NULLS LAST LIMIT 80
    """))).mappings().all()
    cand_list = [{"id": str(c["id"]), "title": c["title"], "year": c["release_year"],
                  "type": c["type"], "desc": (c["description"] or "")[:180]} for c in cands]

    selected_ids: list[str] = []
    if llm.enabled:
        parsed = await llm.complete_json(
            system=("You are a curator. Given a user's theme prompt and a catalog of titles, "
                    "pick 12 to 18 titles that best fit the theme. Return JSON: "
                    "{\"ids\": [\"id1\",\"id2\",...], \"reason\": \"one short sentence\"}. "
                    "Only pick from provided ids."),
            user=json.dumps({"theme": body.prompt, "catalog": cand_list}),
            max_tokens=500, temperature=0.4,
        )
        if parsed and isinstance(parsed.get("ids"), list):
            selected_ids = [i for i in parsed["ids"] if any(c["id"] == i for c in cand_list)]

    if not selected_ids:
        # Fallback: naive keyword match
        words = [w for w in body.prompt.lower().split() if len(w) > 3]
        selected_ids = [c["id"] for c in cand_list
                        if any(w in (c["desc"] + " " + c["title"]).lower() for w in words)][:15]

    await db.execute(text("""
        INSERT INTO ai_collections (user_id, name, prompt, content_ids, is_public)
        VALUES (:u, :n, :p, CAST(:ids AS uuid[]), :pub)
    """), {"u": str(user.id), "n": body.name, "p": body.prompt,
           "ids": selected_ids, "pub": body.is_public})
    await db.commit()
    return {"status": "ok", "count": len(selected_ids), "content_ids": selected_ids}


@router.get("/ai-collections")
async def list_ai_collections(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, name, prompt, content_ids, is_public, created_at
        FROM ai_collections WHERE user_id = :u OR is_public = true
        ORDER BY created_at DESC LIMIT 40
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"]),
                       "content_ids": [str(x) for x in r["content_ids"] or []]} for r in rows]}


# ─────────────────────────────────────────────────────────
# 3. AUTO-TAGGING (admin-triggered batch)
# ─────────────────────────────────────────────────────────
@router.post("/admin/auto-tag")
async def auto_tag(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    llm = get_llm()
    if not llm.enabled:
        raise HTTPException(status_code=503, detail="LLM not configured")
    # pick titles whose vibe looks default-ish (close to 0.5 across all dims)
    rows = (await db.execute(text("""
        SELECT id, title, description, genre_ids FROM content
        WHERE is_active = true
          AND abs(vibe_pace - 0.5) + abs(vibe_emotion - 0.5) + abs(vibe_darkness - 0.5) < 0.4
        ORDER BY popularity_score DESC LIMIT :lim
    """), {"lim": limit})).mappings().all()
    updated = 0
    for r in rows:
        parsed = await llm.complete_json(
            system=("Score this title on 6 dims 0..1: pace, emotion, darkness, humor, complexity, spectacle. "
                    "Respond JSON: {pace, emotion, darkness, humor, complexity, spectacle}."),
            user=f"Title: {r['title']}\nDesc: {r['description']}",
            max_tokens=120, temperature=0.1,
        )
        if not parsed:
            continue
        try:
            await db.execute(text("""
                UPDATE content SET
                    vibe_pace = :pace, vibe_emotion = :emotion, vibe_darkness = :darkness,
                    vibe_humor = :humor, vibe_complexity = :complexity, vibe_spectacle = :spectacle
                WHERE id = :id
            """), {**{k: float(parsed.get(k, 0.5)) for k in VIBE_DIMS}, "id": str(r["id"])})
            updated += 1
        except Exception:
            continue
    await db.commit()
    return {"updated": updated, "sampled": len(rows)}


# ─────────────────────────────────────────────────────────
# 4. FRIENDS
# ─────────────────────────────────────────────────────────
class FollowIn(BaseModel):
    friend_id: uuid.UUID


@router.post("/users/me/friends")
async def follow(
    body: FollowIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.friend_id == user.id:
        raise HTTPException(status_code=400, detail="cannot friend yourself")
    await db.execute(text("""
        INSERT INTO friendships (user_id, friend_id, status)
        VALUES (:u, :f, 'accepted')
        ON CONFLICT DO NOTHING
    """), {"u": str(user.id), "f": str(body.friend_id)})
    await db.commit()
    return {"status": "ok"}


@router.delete("/users/me/friends/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(
    friend_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("DELETE FROM friendships WHERE user_id=:u AND friend_id=:f"),
                     {"u": str(user.id), "f": str(friend_id)})
    await db.commit()


@router.get("/users/me/friends")
async def list_friends(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT u.id, u.display_name, u.email, u.dna_samples
        FROM friendships f JOIN users u ON u.id = f.friend_id
        WHERE f.user_id = :u AND f.status = 'accepted'
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"])} for r in rows]}


@router.get("/users/me/friends/activity")
async def friends_activity(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
):
    rows = (await db.execute(text("""
        SELECT u.display_name, c.title, c.id as content_id, c.thumbnail_url, w.last_watched_at, w.watch_pct
        FROM friendships f
        JOIN watch_history w ON w.user_id = f.friend_id
        JOIN users u ON u.id = f.friend_id
        JOIN content c ON c.id = w.content_id
        WHERE f.user_id = :u AND f.status = 'accepted'
        ORDER BY w.last_watched_at DESC LIMIT :lim
    """), {"u": str(user.id), "lim": limit})).mappings().all()
    return {"items": [{**r, "content_id": str(r["content_id"]),
                       "last_watched_at": r["last_watched_at"].isoformat()} for r in rows]}


# ─────────────────────────────────────────────────────────
# 5. TASTE TWINS — users with most similar DNA
# ─────────────────────────────────────────────────────────
@router.get("/users/me/taste-twins")
async def taste_twins(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    user_dna = [float(getattr(user, f"dna_{d}")) for d in VIBE_DIMS]
    # Squared L2 distance in SQL
    dist_expr = " + ".join([f"power(u.dna_{d} - :d{i}, 2)" for i, d in enumerate(VIBE_DIMS)])
    params = {f"d{i}": user_dna[i] for i in range(len(VIBE_DIMS))}
    params["uid"] = str(user.id)
    params["lim"] = limit
    rows = (await db.execute(text(f"""
        SELECT u.id, u.display_name, u.dna_samples,
               sqrt({dist_expr}) AS dist
        FROM users u
        WHERE u.id != :uid AND u.dna_samples > 5
        ORDER BY dist ASC LIMIT :lim
    """), params)).mappings().all()
    return {"items": [{"id": str(r["id"]), "display_name": r["display_name"],
                       "dna_samples": r["dna_samples"],
                       "similarity": round(1 - min(float(r["dist"]) / 2.449, 1), 3)} for r in rows]}


# ─────────────────────────────────────────────────────────
# 6. SHARED WATCHLISTS
# ─────────────────────────────────────────────────────────
class SharedListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


@router.post("/shared-lists")
async def create_shared_list(
    body: SharedListCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token = secrets.token_urlsafe(12)
    r = await db.execute(text("""
        INSERT INTO shared_watchlists (owner_id, name, share_token)
        VALUES (:o, :n, :t) RETURNING id
    """), {"o": str(user.id), "n": body.name, "t": token})
    wid = r.scalar_one()
    await db.execute(text(
        "INSERT INTO shared_watchlist_members (watchlist_id, user_id) VALUES (:w, :u)"
    ), {"w": str(wid), "u": str(user.id)})
    await db.commit()
    return {"id": str(wid), "share_token": token, "share_url": f"/shared/{token}"}


@router.get("/shared-lists")
async def list_shared_lists(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT sw.id, sw.name, sw.share_token, sw.created_at,
               (SELECT COUNT(*) FROM shared_watchlist_items i WHERE i.watchlist_id = sw.id) AS count
        FROM shared_watchlists sw
        JOIN shared_watchlist_members m ON m.watchlist_id = sw.id
        WHERE m.user_id = :u ORDER BY sw.created_at DESC
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"]), "count": int(r["count"])} for r in rows]}


@router.post("/shared-lists/join/{token}")
async def join_shared_list(
    token: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(text("SELECT id FROM shared_watchlists WHERE share_token=:t"), {"t": token})
    wid = r.scalar_one_or_none()
    if wid is None:
        raise HTTPException(status_code=404, detail="not found")
    await db.execute(text("""
        INSERT INTO shared_watchlist_members (watchlist_id, user_id)
        VALUES (:w, :u) ON CONFLICT DO NOTHING
    """), {"w": str(wid), "u": str(user.id)})
    await db.commit()
    return {"watchlist_id": str(wid)}


# ─────────────────────────────────────────────────────────
# 7. REVIEWS + COMMENTS
# ─────────────────────────────────────────────────────────
class ReviewIn(BaseModel):
    content_id: uuid.UUID
    body: str = Field(min_length=1, max_length=4000)
    has_spoilers: bool = False


@router.post("/reviews")
async def create_review(
    body: ReviewIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(text("""
        INSERT INTO reviews (user_id, content_id, body, has_spoilers)
        VALUES (:u, :c, :b, :s) RETURNING id
    """), {"u": str(user.id), "c": str(body.content_id), "b": body.body, "s": body.has_spoilers})
    await db.commit()
    return {"id": str(r.scalar_one())}


@router.get("/content/{content_id}/reviews")
async def list_reviews(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT r.id, r.body, r.has_spoilers, r.upvotes, r.created_at, u.display_name
        FROM reviews r JOIN users u ON u.id = r.user_id
        WHERE r.content_id = :c ORDER BY r.upvotes DESC, r.created_at DESC LIMIT 40
    """), {"c": str(content_id)})).mappings().all()
    return {"items": [{**r, "id": str(r["id"]),
                       "created_at": r["created_at"].isoformat()} for r in rows]}


# ─────────────────────────────────────────────────────────
# 8. MULTI-PROFILES (Netflix-style)
# ─────────────────────────────────────────────────────────
class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    avatar_emoji: str = Field(default="🎬", max_length=10)
    is_kid: bool = False
    pin: str | None = Field(default=None, min_length=4, max_length=8)
    max_maturity: str = "R"


@router.get("/profiles")
async def list_profiles(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, name, avatar_emoji, is_kid, max_maturity, (pin_hash IS NOT NULL) as has_pin
        FROM profiles WHERE user_id=:u ORDER BY created_at
    """), {"u": str(user.id)})).mappings().all()
    items = [{**r, "id": str(r["id"])} for r in rows]
    if not items:
        # seed a default "Main" profile
        await db.execute(text("""
            INSERT INTO profiles (user_id, name, avatar_emoji) VALUES (:u, 'Main', '🎬')
        """), {"u": str(user.id)})
        await db.commit()
        return await list_profiles(user, db)
    return {"items": items}


@router.post("/profiles")
async def create_profile(
    body: ProfileIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pin_hash = hashlib.sha256(body.pin.encode()).hexdigest() if body.pin else None
    r = await db.execute(text("""
        INSERT INTO profiles (user_id, name, avatar_emoji, is_kid, pin_hash, max_maturity)
        VALUES (:u, :n, :a, :k, :p, :m) RETURNING id
    """), {"u": str(user.id), "n": body.name, "a": body.avatar_emoji,
           "k": body.is_kid, "p": pin_hash, "m": body.max_maturity})
    await db.commit()
    return {"id": str(r.scalar_one())}


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("DELETE FROM profiles WHERE id=:p AND user_id=:u"),
                     {"p": str(profile_id), "u": str(user.id)})
    await db.commit()


# ─────────────────────────────────────────────────────────
# 9. EPISODES (pulled on-demand from TVMaze when available)
# ─────────────────────────────────────────────────────────
@router.get("/content/{content_id}/episodes")
async def list_episodes(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, season, number, title, description, duration_seconds, aired_at, thumbnail_url
        FROM episodes WHERE content_id=:c ORDER BY season, number LIMIT 200
    """), {"c": str(content_id)})).mappings().all()
    if rows:
        return {"items": [{**r, "id": str(r["id"]),
                           "aired_at": r["aired_at"].isoformat() if r["aired_at"] else None} for r in rows]}
    # No episodes yet — return stub that frontend can display
    return {"items": [], "hint": "Episode data not ingested — run the TVMaze episode hydrator."}


# ─────────────────────────────────────────────────────────
# 10. CAST / PERSON
# ─────────────────────────────────────────────────────────
@router.get("/persons/{person_id}")
async def person_detail(
    person_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    p = (await db.execute(text("SELECT * FROM persons WHERE id=:p"),
                          {"p": str(person_id)})).mappings().first()
    if not p:
        raise HTTPException(status_code=404, detail="not found")
    credits = (await db.execute(text("""
        SELECT c.id, c.title, c.thumbnail_url, cr.role, cr.character
        FROM credits cr JOIN content c ON c.id = cr.content_id
        WHERE cr.person_id=:p ORDER BY cr.position
    """), {"p": str(person_id)})).mappings().all()
    return {"person": {**p, "id": str(p["id"])},
            "credits": [{**cr, "id": str(cr["id"])} for cr in credits]}


# ─────────────────────────────────────────────────────────
# 11. WATCH PARTY
# ─────────────────────────────────────────────────────────
class PartyCreate(BaseModel):
    content_id: uuid.UUID


@router.post("/watch-parties")
async def create_party(
    body: PartyCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    code = secrets.token_urlsafe(6)[:8].upper()
    r = await db.execute(text("""
        INSERT INTO watch_parties (host_id, content_id, room_code)
        VALUES (:h, :c, :r) RETURNING id
    """), {"h": str(user.id), "c": str(body.content_id), "r": code})
    await db.commit()
    return {"id": str(r.scalar_one()), "room_code": code}


class PartyState(BaseModel):
    position: float = Field(ge=0)
    is_playing: bool


@router.post("/watch-parties/{room_code}/state")
async def update_party_state(
    room_code: str,
    body: PartyState,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        UPDATE watch_parties SET current_position=:p, is_playing=:pl
        WHERE room_code=:r AND host_id=:u
    """), {"p": body.position, "pl": body.is_playing, "r": room_code, "u": str(user.id)})
    await db.commit()
    return {"status": "ok"}


@router.get("/watch-parties/{room_code}")
async def get_party(
    room_code: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    p = (await db.execute(text(
        "SELECT * FROM watch_parties WHERE room_code=:r"
    ), {"r": room_code})).mappings().first()
    if not p:
        raise HTTPException(status_code=404, detail="not found")
    return {**p, "id": str(p["id"]),
            "host_id": str(p["host_id"]), "content_id": str(p["content_id"]),
            "started_at": p["started_at"].isoformat()}


# ─────────────────────────────────────────────────────────
# 12. NOTIFICATIONS
# ─────────────────────────────────────────────────────────
@router.get("/users/me/notifications")
async def list_notifs(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = Query(False),
):
    q = "SELECT id, kind, title, body, link, read, created_at FROM notifications WHERE user_id=:u"
    if unread_only:
        q += " AND read=false"
    q += " ORDER BY created_at DESC LIMIT 50"
    rows = (await db.execute(text(q), {"u": str(user.id)})).mappings().all()
    return {"items": [{**r, "created_at": r["created_at"].isoformat()} for r in rows]}


@router.post("/users/me/notifications/read-all")
async def mark_all_read(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("UPDATE notifications SET read=true WHERE user_id=:u"),
                     {"u": str(user.id)})
    await db.commit()
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────
# 13. A/B EXPERIMENTS
# ─────────────────────────────────────────────────────────
@router.get("/users/me/experiments")
async def my_experiments(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT e.name, a.variant FROM ab_assignments a
        JOIN ab_experiments e ON e.id = a.experiment_id
        WHERE a.user_id = :u AND e.is_active = true
    """), {"u": str(user.id)})).mappings().all()
    return {"items": [dict(r) for r in rows]}


# ─────────────────────────────────────────────────────────
# 14. COHORT RETENTION (admin)
# ─────────────────────────────────────────────────────────
@router.get("/admin/analytics/retention")
async def retention(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        WITH signups AS (
            SELECT id, date_trunc('day', created_at)::date AS cohort FROM users
        ),
        events_per_day AS (
            SELECT user_id, date_trunc('day', created_at)::date AS day FROM interactions
            GROUP BY user_id, day
        )
        SELECT s.cohort,
               COUNT(DISTINCT s.id) AS cohort_size,
               COUNT(DISTINCT e1.user_id) FILTER (WHERE e1.day = s.cohort + 1) AS d1,
               COUNT(DISTINCT e1.user_id) FILTER (WHERE e1.day = s.cohort + 7) AS d7,
               COUNT(DISTINCT e1.user_id) FILTER (WHERE e1.day = s.cohort + 30) AS d30
        FROM signups s LEFT JOIN events_per_day e1 ON e1.user_id = s.id
        GROUP BY s.cohort ORDER BY s.cohort DESC LIMIT 14
    """))).mappings().all()
    return {"cohorts": [{**r, "cohort": r["cohort"].isoformat()} for r in rows]}


# ─────────────────────────────────────────────────────────
# 15. DATA EXPORT
# ─────────────────────────────────────────────────────────
@router.post("/users/me/export")
async def request_export(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Synchronous inline export (small per-user data).
    history = (await db.execute(text("""
        SELECT content_id, watch_pct, completed, last_watched_at
        FROM watch_history WHERE user_id=:u
    """), {"u": str(user.id)})).mappings().all()
    ratings = (await db.execute(text("""
        SELECT content_id, rating, mood_tag, note, rated_at FROM ratings WHERE user_id=:u
    """), {"u": str(user.id)})).mappings().all()
    feedback = (await db.execute(text("""
        SELECT content_id, surface, feedback, created_at FROM rec_feedback WHERE user_id=:u
    """), {"u": str(user.id)})).mappings().all()

    def ser(x):
        if isinstance(x, datetime): return x.isoformat()
        if isinstance(x, uuid.UUID): return str(x)
        return x

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": str(user.id), "email": user.email, "display_name": user.display_name},
        "taste_dna": {d: float(getattr(user, f"dna_{d}")) for d in VIBE_DIMS},
        "dna_samples": user.dna_samples,
        "watch_history": [{k: ser(v) for k, v in r.items()} for r in history],
        "ratings": [{k: ser(v) for k, v in r.items()} for r in ratings],
        "rec_feedback": [{k: ser(v) for k, v in r.items()} for r in feedback],
    }
    return payload


# ─────────────────────────────────────────────────────────
# 16. BILLING / ENTITLEMENTS STUB
# ─────────────────────────────────────────────────────────
@router.get("/users/me/entitlements")
async def entitlements(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text("SELECT * FROM entitlements WHERE user_id=:u"),
                            {"u": str(user.id)})).mappings().first()
    if not row:
        await db.execute(text("INSERT INTO entitlements (user_id) VALUES (:u)"),
                         {"u": str(user.id)})
        await db.commit()
        return {"tier": "free", "ai_quota_daily": 50, "ai_used_today": 0}
    return dict(row) | {"user_id": str(row["user_id"]),
                        "renewed_at": row["renewed_at"].isoformat()}


# ─────────────────────────────────────────────────────────
# 17. TASTE-TWIN RECOMMENDATIONS (what your twins watched)
# ─────────────────────────────────────────────────────────
@router.get("/users/me/twin-picks")
async def twin_picks(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=50),
):
    user_dna = [float(getattr(user, f"dna_{d}")) for d in VIBE_DIMS]
    dist_expr = " + ".join([f"power(u.dna_{d} - :d{i}, 2)" for i, d in enumerate(VIBE_DIMS)])
    params = {f"d{i}": user_dna[i] for i in range(len(VIBE_DIMS))}
    params["uid"] = str(user.id)
    params["lim"] = limit
    rows = (await db.execute(text(f"""
        WITH twins AS (
            SELECT u.id FROM users u
            WHERE u.id != :uid AND u.dna_samples > 5
            ORDER BY {dist_expr} ASC LIMIT 5
        )
        SELECT c.id, c.title, c.thumbnail_url, c.release_year, COUNT(w.user_id) AS twin_count
        FROM twins t JOIN watch_history w ON w.user_id = t.id
        JOIN content c ON c.id = w.content_id
        WHERE NOT EXISTS (
            SELECT 1 FROM watch_history wh WHERE wh.user_id = :uid AND wh.content_id = c.id
        )
        GROUP BY c.id ORDER BY twin_count DESC LIMIT :lim
    """), params)).mappings().all()
    return {"items": [{**r, "id": str(r["id"]), "twin_count": int(r["twin_count"])} for r in rows]}
