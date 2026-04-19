"""Perf: batched + rec-quality + moderation + newsletter + referrals endpoints."""
import secrets
import uuid
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user, require_admin
from models.user import User

router = APIRouter(tags=["batch"])


# ─── Batched recommendations (one request → N surfaces) ──
class BatchRecIn(BaseModel):
    surfaces: list[str] = Field(min_length=1, max_length=12)
    limit: int = Field(default=20, ge=1, le=50)


@router.post("/recommendations/batch")
async def batch_recs(
    body: BatchRecIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from repositories.content_repo import ContentRepo
    from repositories.interaction_repo import InteractionRepo
    from repositories.recommendation_repo import RecommendationRepo
    from services.cache_service import CacheService
    from services.recommendation_service import RecommendationService
    from core.redis import get_redis
    redis = await get_redis()
    svc = RecommendationService(ContentRepo(db), InteractionRepo(db), RecommendationRepo(db), CacheService(redis))
    import asyncio
    results = await asyncio.gather(*[
        svc.get_recommendations(user.id, s, limit=body.limit, offset=0)
        for s in body.surfaces
    ], return_exceptions=True)
    out = {}
    for surface, res in zip(body.surfaces, results):
        if isinstance(res, Exception):
            out[surface] = {"error": str(res)}
        else:
            out[surface] = res.model_dump()
    return {"surfaces": out}


# ─── Rec quality metrics (admin) ─────────────────────────
@router.get("/admin/analytics/rec-quality")
async def rec_quality(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(14, ge=1, le=90),
):
    rows = (await db.execute(text("""
        SELECT day, surface, impressions, clicks, plays, completes, likes, dislikes
        FROM rec_quality_daily
        WHERE day >= current_date - :days
        ORDER BY day DESC, surface
    """), {"days": days})).mappings().all()
    out = []
    for r in rows:
        imp = max(r["impressions"], 1)
        out.append({
            **r, "day": r["day"].isoformat(),
            "ctr": round(r["clicks"] / imp, 3),
            "play_rate": round(r["plays"] / imp, 3),
            "complete_rate": round(r["completes"] / max(r["plays"], 1), 3),
            "net_sentiment": round((r["likes"] - r["dislikes"]) / max(r["likes"] + r["dislikes"], 1), 3),
        })
    return {"items": out}


# ─── Moderation ─────────────────────────────────────────
class FlagIn(BaseModel):
    target_type: str
    target_id: str
    reason: str = Field(max_length=300)


@router.post("/moderation/flag")
async def flag(
    body: FlagIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(text("""
        INSERT INTO moderation_flags (target_type, target_id, reporter_id, reason)
        VALUES (:t, :i, :u, :r)
    """), {"t": body.target_type, "i": body.target_id, "u": str(user.id), "r": body.reason})
    await db.commit()
    return {"status": "flagged"}


@router.get("/admin/moderation/queue")
async def mod_queue(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(text("""
        SELECT id, target_type, target_id, reason, status, created_at, reporter_id
        FROM moderation_flags WHERE status='pending' ORDER BY created_at DESC LIMIT 50
    """))).mappings().all()
    return {"items": [{**r, "created_at": r["created_at"].isoformat(),
                       "reporter_id": str(r["reporter_id"]) if r["reporter_id"] else None} for r in rows]}


@router.post("/admin/moderation/resolve/{flag_id}")
async def resolve_flag(
    flag_id: int,
    action: str = Query("dismiss", pattern="^(dismiss|delete|ban)$"),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("UPDATE moderation_flags SET status=:s WHERE id=:i"),
                     {"s": action, "i": flag_id})
    await db.commit()
    return {"status": "ok"}


# ─── Newsletter ─────────────────────────────────────────
class NewsletterIn(BaseModel):
    email: EmailStr


@router.post("/newsletter/subscribe")
async def subscribe(body: NewsletterIn, db: Annotated[AsyncSession, Depends(get_db)]):
    await db.execute(text("""
        INSERT INTO newsletter_subscribers (email) VALUES (:e)
        ON CONFLICT (email) DO UPDATE SET unsubscribed=false
    """), {"e": body.email})
    await db.commit()
    return {"status": "subscribed"}


@router.post("/newsletter/unsubscribe")
async def unsubscribe(body: NewsletterIn, db: Annotated[AsyncSession, Depends(get_db)]):
    await db.execute(text("UPDATE newsletter_subscribers SET unsubscribed=true WHERE email=:e"),
                     {"e": body.email})
    await db.commit()
    return {"status": "unsubscribed"}


# ─── Referrals ──────────────────────────────────────────
@router.post("/referrals/create")
async def create_ref(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    code = secrets.token_urlsafe(6)[:8].upper()
    await db.execute(text("""
        INSERT INTO referrals (referrer_id, code) VALUES (:u, :c)
    """), {"u": str(user.id), "c": code})
    await db.commit()
    return {"code": code, "share_url": f"/register?ref={code}"}


@router.post("/referrals/redeem/{code}")
async def redeem_ref(
    code: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text(
        "SELECT id, referrer_id, uses, max_uses FROM referrals WHERE code=:c"
    ), {"c": code})).first()
    if not row:
        raise HTTPException(status_code=404, detail="invalid code")
    _, referrer, uses, max_uses = row
    if uses >= max_uses:
        raise HTTPException(status_code=400, detail="code exhausted")
    if str(referrer) == str(user.id):
        raise HTTPException(status_code=400, detail="cannot redeem own code")
    await db.execute(text("""
        INSERT INTO referral_redemptions (code, redeemer_id) VALUES (:c, :u)
        ON CONFLICT DO NOTHING
    """), {"c": code, "u": str(user.id)})
    await db.execute(text("UPDATE referrals SET uses=uses+1 WHERE code=:c"), {"c": code})
    # badge both
    await db.execute(text("""
        UPDATE user_streaks SET badges = array_append(badges, 'referral')
        WHERE user_id=:u AND NOT ('referral' = ANY(badges))
    """), {"u": str(user.id)})
    await db.execute(text("""
        UPDATE user_streaks SET badges = array_append(badges, 'referrer')
        WHERE user_id=:r AND NOT ('referrer' = ANY(badges))
    """), {"r": str(referrer)})
    await db.commit()
    return {"status": "ok"}


# ─── Search autocomplete (trgm-indexed) ─────────────────
@router.get("/search/suggest")
async def suggest(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(min_length=1, max_length=80),
    limit: int = Query(8, ge=1, le=20),
):
    pattern = f"%{q.lower()}%"
    rows = (await db.execute(text("""
        SELECT id, title, type, release_year, thumbnail_url, popularity_score
        FROM content
        WHERE is_active = true AND lower(title) LIKE :p
        ORDER BY
          CASE WHEN lower(title) = lower(:q) THEN 0
               WHEN lower(title) LIKE lower(:q) || '%' THEN 1
               ELSE 2 END,
          popularity_score DESC
        LIMIT :lim
    """), {"p": pattern, "q": q, "lim": limit})).mappings().all()
    # crude similarity score for highlighting
    return {"query": q, "items": [{
        "id": str(r["id"]), "title": r["title"], "type": r["type"],
        "release_year": r["release_year"], "thumbnail_url": r["thumbnail_url"],
        "sim": 1.0 if q.lower() in (r["title"] or "").lower() else 0.5,
    } for r in rows]}


# ─── Health: liveness + readiness ──────────────────────
@router.get("/health/live")
async def live(): return {"status": "live"}


@router.get("/health/ready")
async def ready(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready"}


# ─── Admin content editor ───────────────────────────────
class ContentEdit(BaseModel):
    title: str | None = None
    description: str | None = None
    maturity_rating: str | None = None
    thumbnail_url: str | None = None
    trailer_url: str | None = None


@router.put("/admin/content/{content_id}")
async def admin_edit_content(
    content_id: uuid.UUID,
    body: ContentEdit,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        return {"status": "noop"}
    set_sql = ", ".join([f"{k}=:{k}" for k in fields])
    await db.execute(text(f"UPDATE content SET {set_sql} WHERE id=:id"),
                     {**fields, "id": str(content_id)})
    await db.execute(text("""
        INSERT INTO audit_events (actor_id, action, target_type, target_id)
        VALUES (NULL, 'admin_edit_content', 'content', :c)
    """), {"c": str(content_id)})
    await db.commit()
    return {"status": "ok", "fields_updated": list(fields.keys())}
