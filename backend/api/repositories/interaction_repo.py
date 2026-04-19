import uuid
from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.interaction import Interaction
from models.watch_history import WatchHistory
from models.rating import Rating, Watchlist


class InteractionRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_batch(self, events: list[dict]) -> int:
        if not events:
            return 0
        now = datetime.now(timezone.utc)
        rows = [
            Interaction(
                user_id=e["user_id"],
                content_id=e["content_id"],
                event_type=e["event_type"],
                value=e.get("value"),
                session_id=e.get("session_id"),
                device_type=e.get("device_type"),
                created_at=e.get("timestamp") or now,
            )
            for e in events
            if e.get("content_id") is not None
        ]
        self.session.add_all(rows)
        await self.session.commit()
        return len(rows)

    async def recent_for_user(self, user_id: uuid.UUID, limit: int = 50) -> list[Interaction]:
        res = await self.session.execute(
            select(Interaction).where(Interaction.user_id == user_id)
            .order_by(desc(Interaction.created_at)).limit(limit)
        )
        return list(res.scalars().all())

    async def continue_watching(self, user_id: uuid.UUID, limit: int = 20) -> list[WatchHistory]:
        res = await self.session.execute(
            select(WatchHistory).where(
                WatchHistory.user_id == user_id,
                WatchHistory.completed == False,
                WatchHistory.watch_pct > 0.05,
                WatchHistory.watch_pct < 0.95,
            ).order_by(desc(WatchHistory.last_watched_at)).limit(limit)
        )
        return list(res.scalars().all())

    async def watch_history(self, user_id: uuid.UUID, limit: int = 100) -> list[WatchHistory]:
        res = await self.session.execute(
            select(WatchHistory).where(WatchHistory.user_id == user_id)
            .order_by(desc(WatchHistory.last_watched_at)).limit(limit)
        )
        return list(res.scalars().all())

    async def watchlist(self, user_id: uuid.UUID) -> list[Watchlist]:
        res = await self.session.execute(
            select(Watchlist).where(Watchlist.user_id == user_id).order_by(desc(Watchlist.added_at))
        )
        return list(res.scalars().all())

    async def add_to_watchlist(self, user_id: uuid.UUID, content_id: uuid.UUID) -> None:
        existing = await self.session.execute(
            select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.content_id == content_id)
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(Watchlist(user_id=user_id, content_id=content_id))
            await self.session.commit()

    async def upsert_rating(
        self,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
        rating: int,
        mood_tag: str | None = None,
        note: str | None = None,
    ) -> Rating:
        res = await self.session.execute(
            select(Rating).where(Rating.user_id == user_id, Rating.content_id == content_id)
        )
        r = res.scalar_one_or_none()
        if r is None:
            r = Rating(user_id=user_id, content_id=content_id, rating=rating, mood_tag=mood_tag, note=note)
            self.session.add(r)
        else:
            r.rating = rating
            if mood_tag is not None:
                r.mood_tag = mood_tag
            if note is not None:
                r.note = note
        await self.session.commit()
        await self.session.refresh(r)
        return r

    async def ratings(self, user_id: uuid.UUID) -> list[Rating]:
        res = await self.session.execute(
            select(Rating).where(Rating.user_id == user_id).order_by(desc(Rating.rated_at))
        )
        return list(res.scalars().all())
