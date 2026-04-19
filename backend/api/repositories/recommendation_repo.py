import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recommendation import RecommendationSnapshot


class RecommendationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID, surface: str) -> RecommendationSnapshot | None:
        res = await self.session.execute(
            select(RecommendationSnapshot).where(
                RecommendationSnapshot.user_id == user_id,
                RecommendationSnapshot.surface == surface,
            )
        )
        return res.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        surface: str,
        content_ids: list[uuid.UUID],
        scores: list[float],
        model_version: str,
        ttl_minutes: int = 60,
    ) -> RecommendationSnapshot:
        existing = await self.get(user_id, surface)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ttl_minutes)
        if existing is None:
            snap = RecommendationSnapshot(
                user_id=user_id, surface=surface, content_ids=content_ids, scores=scores,
                model_version=model_version, generated_at=now, expires_at=expires,
            )
            self.session.add(snap)
        else:
            existing.content_ids = content_ids
            existing.scores = scores
            existing.model_version = model_version
            existing.generated_at = now
            existing.expires_at = expires
            snap = existing
        await self.session.commit()
        await self.session.refresh(snap)
        return snap
