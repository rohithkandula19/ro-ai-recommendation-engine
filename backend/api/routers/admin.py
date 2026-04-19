from typing import Annotated
from fastapi import APIRouter, Depends, Query
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from core.database import get_db
from middleware.auth_middleware import require_admin
from models.user import User
from services.analytics_service import AnalyticsService
from tasks.celery_app import celery_app

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics")
async def admin_metrics(_: Annotated[User, Depends(require_admin)]):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/model/retrain")
async def retrain(_: Annotated[User, Depends(require_admin)]):
    task = celery_app.send_task("tasks.retrain_task.retrain_all")
    return {"task_id": task.id, "status": "queued"}


@router.get("/analytics/overview")
async def analytics_overview(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AnalyticsService(db).overview()


@router.get("/analytics/top-content")
async def analytics_top_content(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    return {"items": await AnalyticsService(db).top_content(limit)}


@router.get("/analytics/events-timeseries")
async def analytics_events_timeseries(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(14, ge=1, le=90),
):
    return {"days": days, "series": await AnalyticsService(db).events_timeseries(days)}


@router.get("/analytics/top-genres")
async def analytics_top_genres(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    return {"items": await AnalyticsService(db).top_genres(limit)}
