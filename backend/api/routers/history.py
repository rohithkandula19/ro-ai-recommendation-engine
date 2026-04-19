import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from repositories.interaction_repo import InteractionRepo

router = APIRouter(prefix="/users/me", tags=["history"])


class HistoryItem(BaseModel):
    content_id: uuid.UUID
    watch_pct: float
    total_seconds_watched: int
    completed: bool
    last_watched_at: str


class WatchlistItem(BaseModel):
    content_id: uuid.UUID
    added_at: str


class RateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    mood_tag: str | None = Field(default=None, max_length=40)
    note: str | None = Field(default=None, max_length=500)


@router.get("/history", response_model=list[HistoryItem])
async def history(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
):
    repo = InteractionRepo(db)
    h = await repo.watch_history(user.id, limit=limit)
    return [
        HistoryItem(
            content_id=x.content_id, watch_pct=x.watch_pct,
            total_seconds_watched=x.total_seconds_watched, completed=x.completed,
            last_watched_at=x.last_watched_at.isoformat(),
        ) for x in h
    ]


@router.get("/watchlist", response_model=list[WatchlistItem])
async def watchlist(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = InteractionRepo(db)
    w = await repo.watchlist(user.id)
    return [WatchlistItem(content_id=x.content_id, added_at=x.added_at.isoformat()) for x in w]


@router.post("/watchlist/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_watchlist(
    content_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = InteractionRepo(db)
    await repo.add_to_watchlist(user.id, content_id)


@router.post("/ratings/{content_id}", status_code=status.HTTP_201_CREATED)
async def rate(
    content_id: uuid.UUID,
    body: RateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = InteractionRepo(db)
    r = await repo.upsert_rating(user.id, content_id, body.rating, body.mood_tag, body.note)
    return {
        "user_id": str(r.user_id),
        "content_id": str(r.content_id),
        "rating": r.rating,
        "mood_tag": r.mood_tag,
        "note": r.note,
    }
