from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis import get_redis
from middleware.auth_middleware import get_current_user
from models.user import User
from repositories.interaction_repo import InteractionRepo
from schemas.event import EventBatch, EventIngestResponse
from services.cache_service import CacheService
from services.event_service import EventService
from tasks.rec_quality_tracker import track as rq_track

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/ingest", response_model=EventIngestResponse)
async def ingest(
    body: EventBatch,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    redis_client = await get_redis()
    svc = EventService(InteractionRepo(db), CacheService(redis_client))
    events = [e.model_dump() for e in body.events]
    accepted, rejected = await svc.ingest(events)
    # rec-quality tracker (bucket by event_type; surface extracted from value payload if present)
    for e in events:
        surface = None
        try:
            if isinstance(e.get("value"), dict):
                surface = e["value"].get("surface")
        except Exception:
            pass
        await rq_track(db, e.get("event_type", ""), surface or "home")
    await db.commit()
    return EventIngestResponse(accepted=accepted, rejected=rejected)
