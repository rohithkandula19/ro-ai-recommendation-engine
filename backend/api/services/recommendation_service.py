import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger

from core.config import settings
from repositories.content_repo import ContentRepo
from repositories.interaction_repo import InteractionRepo
from repositories.recommendation_repo import RecommendationRepo
from schemas.recommendation import RecommendationItem, RecommendationResponse
from services.cache_service import CacheService


REASON_BY_SURFACE = {
    "home": "Recommended for you",
    "trending": "Trending this week",
    "because_you_watched": "Because you watched something similar",
    "continue_watching": "Pick up where you left off",
    "new_releases": "New release",
}


class RecommendationService:
    def __init__(
        self,
        content_repo: ContentRepo,
        interaction_repo: InteractionRepo,
        rec_repo: RecommendationRepo,
        cache: CacheService,
    ):
        self.content_repo = content_repo
        self.interaction_repo = interaction_repo
        self.rec_repo = rec_repo
        self.cache = cache

    async def get_recommendations(
        self, user_id: uuid.UUID, surface: str, limit: int = 20, offset: int = 0
    ) -> RecommendationResponse:
        cache_key = f"rec:{user_id}:{surface}:{limit}:{offset}"
        cached = await self.cache.get_json(cache_key)
        if cached:
            return RecommendationResponse(**cached)

        items = await self._build(user_id, surface, limit, offset)
        response = RecommendationResponse(
            surface=surface,
            items=items,
            generated_at=datetime.now(timezone.utc),
            model_version=settings.MODEL_VERSION,
        )
        await self.cache.set_json(cache_key, response.model_dump(), ttl_seconds=300)
        return response

    async def _build(self, user_id: uuid.UUID, surface: str, limit: int, offset: int) -> list[RecommendationItem]:
        if surface == "continue_watching":
            history = await self.interaction_repo.continue_watching(user_id, limit=limit + offset)
            content_ids = [h.content_id for h in history][offset : offset + limit]
            contents = await self.content_repo.get_many(content_ids)
            return [self._to_item(c, score=0.9, surface=surface) for c in contents]

        if surface == "new_releases":
            contents = await self.content_repo.new_releases(limit=limit + offset)
            contents = contents[offset : offset + limit]
            return [self._to_item(c, score=0.7, surface=surface) for c in contents]

        ml_items = await self._call_ml_service(user_id, surface, limit + offset)
        if ml_items:
            content_ids = [uuid.UUID(x["content_id"]) for x in ml_items]
            contents = await self.content_repo.get_many(content_ids)
            id_to_score = {x["content_id"]: x["score"] for x in ml_items}
            pairs = [(c, float(id_to_score.get(str(c.id), 0.0))) for c in contents]
            pairs.sort(key=lambda t: t[1], reverse=True)
            pairs = pairs[offset : offset + limit]

            # Optional AI rerank (no-op when no LLM key set)
            try:
                from services.unique_service import UniqueService
                from core.llm import get_llm
                if get_llm().enabled and surface in {"home", "because_you_watched"}:
                    svc = UniqueService(self.content_repo.session)
                    user = await svc.get_user(user_id)
                    reordered = await svc.ai_rerank(user, [c for c, _ in pairs], limit)
                    return [self._to_item(c, score=id_to_score.get(str(c.id), 0.0), surface=surface) for c in reordered]
            except Exception as e:
                logger.warning(f"AI rerank skipped: {e}")

            return [self._to_item(c, score=s, surface=surface) for c, s in pairs]

        contents = await self.content_repo.trending(limit=limit + offset)
        contents = contents[offset : offset + limit]
        return [self._to_item(c, score=0.5, surface=surface) for c in contents]

    async def _call_ml_service(self, user_id: uuid.UUID, surface: str, limit: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/ml/recommend",
                    json={"user_id": str(user_id), "surface": surface, "limit": limit, "context": {}},
                )
                if resp.status_code == 200:
                    return resp.json().get("items", [])
        except Exception as e:
            logger.warning(f"ML service unavailable: {e}")
        return []

    def _to_item(self, c, score: float, surface: str) -> RecommendationItem:
        score = max(0.0, min(1.0, float(score)))
        return RecommendationItem(
            id=c.id,
            title=c.title,
            type=c.type,
            thumbnail_url=c.thumbnail_url,
            match_score=score,
            reason_text=REASON_BY_SURFACE.get(surface, "Recommended"),
            genre_ids=list(c.genre_ids) if c.genre_ids else [],
        )
