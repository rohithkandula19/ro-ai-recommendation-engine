import time
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis import get_redis
from middleware.auth_middleware import get_current_user
from middleware.metrics_middleware import RECOMMENDATION_LATENCY, RECOMMENDATION_CACHE_HITS
from models.user import User
from repositories.content_repo import ContentRepo
from repositories.interaction_repo import InteractionRepo
from repositories.recommendation_repo import RecommendationRepo
from schemas.recommendation import RecommendationResponse, VALID_SURFACES
from services.cache_service import CacheService
from services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{surface}", response_model=RecommendationResponse)
async def get_recommendations(
    surface: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if surface not in VALID_SURFACES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"surface must be one of {sorted(VALID_SURFACES)}",
        )
    redis_client = await get_redis()
    cache = CacheService(redis_client)
    svc = RecommendationService(
        ContentRepo(db), InteractionRepo(db), RecommendationRepo(db), cache
    )
    start = time.perf_counter()
    cache_key = f"rec:{user.id}:{surface}:{limit}:{offset}"
    had_cache = await cache.get_json(cache_key) is not None
    result = await svc.get_recommendations(user.id, surface, limit=limit, offset=offset)
    RECOMMENDATION_LATENCY.labels(surface=surface).observe(time.perf_counter() - start)
    if had_cache:
        RECOMMENDATION_CACHE_HITS.labels(surface=surface).inc()
    return result
