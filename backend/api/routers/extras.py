"""Final-batch extras: spam reports, review write, reactions, feature flag admin, debug."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user, require_admin
from models.user import User

router = APIRouter(tags=["extras"])


# ─── Spam report on DMs ──────────────────────────────────
class SpamIn(BaseModel):
    target_message_id: int | None = None
    target_user_id: uuid.UUID | None = None
    reason: str = Field(max_length=300)


@router.post("/messages/report-spam")
async def report_spam(
    body: SpamIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target_type = "message" if body.target_message_id else "user"
    target_id = str(body.target_message_id or body.target_user_id)
    await db.execute(text("""
        INSERT INTO moderation_flags (target_type, target_id, reporter_id, reason)
        VALUES (:t, :i, :u, :r)
    """), {"t": target_type, "i": target_id, "u": str(user.id), "r": body.reason})
    await db.commit()
    return {"status": "flagged"}


# ─── Feature flag admin ──────────────────────────────────
@router.get("/admin/feature-flags")
async def list_flags(_: Annotated[User, Depends(require_admin)], db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.execute(text("SELECT key, enabled, rollout_pct, updated_at FROM feature_flags ORDER BY key"))).mappings().all()
    return {"items": [{**r, "updated_at": r["updated_at"].isoformat()} for r in rows]}


# ─── Debug: dump a user's DNA + recent events ────────────
@router.get("/debug/dump-dna/{user_id}")
async def dump_dna(
    user_id: uuid.UUID,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    u = (await db.execute(text("""
        SELECT id, email, display_name, dna_pace, dna_emotion, dna_darkness,
               dna_humor, dna_complexity, dna_spectacle, dna_samples
        FROM users WHERE id=:u
    """), {"u": str(user_id)})).mappings().first()
    if not u:
        raise HTTPException(status_code=404, detail="not found")
    recent = (await db.execute(text("""
        SELECT i.event_type, c.title, i.created_at
        FROM interactions i JOIN content c ON c.id = i.content_id
        WHERE i.user_id=:u ORDER BY i.created_at DESC LIMIT 20
    """), {"u": str(user_id)})).mappings().all()
    return {
        "user": {**u, "id": str(u["id"])},
        "recent_events": [{**r, "created_at": r["created_at"].isoformat()} for r in recent],
    }


# ─── OpenAPI export ──────────────────────────────────────
@router.get("/openapi-export")
async def openapi_export(request):
    """Return the app's openapi spec — useful for external consumers."""
    # Handled by FastAPI's built-in /openapi.json; this is a stable alias.
    from fastapi import Request as _R
    return {"see": "/openapi.json"}


# ─── Review write ────────────────────────────────────────
class WriteReviewIn(BaseModel):
    content_id: uuid.UUID
    body: str = Field(min_length=10, max_length=4000)
    has_spoilers: bool = False


@router.post("/reviews/write")
async def write_review(
    body: WriteReviewIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(text("""
        INSERT INTO reviews (user_id, content_id, body, has_spoilers)
        VALUES (:u, :c, :b, :s) RETURNING id
    """), {"u": str(user.id), "c": str(body.content_id), "b": body.body, "s": body.has_spoilers})
    # push to activity feed
    await db.execute(text("""
        INSERT INTO activity_feed (user_id, kind, content_id, metadata)
        VALUES (:u, 'reviewed', :c, '{}')
    """), {"u": str(user.id), "c": str(body.content_id)})
    await db.commit()
    return {"id": str(r.scalar_one())}
