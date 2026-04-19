from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from services.dna_snapshot_service import DNASnapshotService

router = APIRouter(prefix="/users/me", tags=["dna-timeline"])


@router.get("/dna-timeline")
async def dna_timeline(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(90, ge=7, le=365),
):
    svc = DNASnapshotService(db)
    await svc.snapshot_user(user.id)
    return {"days": days, "points": await svc.timeline(user.id, days)}
