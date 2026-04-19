from __future__ import annotations

import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.queue import WatchQueue, QueueItem


DEFAULT_QUEUES = [
    {"name": "My List", "icon": "📋"},
    {"name": "Workout", "icon": "💪"},
    {"name": "Comfort", "icon": "🛋️"},
    {"name": "Date Night", "icon": "❤️"},
]


class QueueService:
    def __init__(self, s: AsyncSession):
        self.s = s

    async def list(self, user_id: uuid.UUID) -> list[dict]:
        res = await self.s.execute(select(WatchQueue).where(WatchQueue.user_id == user_id).order_by(WatchQueue.created_at))
        qs = list(res.scalars().all())
        if not qs:
            for d in DEFAULT_QUEUES:
                self.s.add(WatchQueue(user_id=user_id, name=d["name"], icon=d["icon"]))
            await self.s.commit()
            res = await self.s.execute(select(WatchQueue).where(WatchQueue.user_id == user_id).order_by(WatchQueue.created_at))
            qs = list(res.scalars().all())

        out = []
        for q in qs:
            count = (await self.s.execute(
                select(QueueItem.content_id).where(QueueItem.queue_id == q.id)
            )).scalars().all()
            out.append({"id": str(q.id), "name": q.name, "icon": q.icon, "count": len(count)})
        return out

    async def create(self, user_id: uuid.UUID, name: str, icon: str | None = None) -> WatchQueue:
        q = WatchQueue(user_id=user_id, name=name, icon=icon)
        self.s.add(q)
        await self.s.commit()
        await self.s.refresh(q)
        return q

    async def delete(self, user_id: uuid.UUID, queue_id: uuid.UUID) -> bool:
        res = await self.s.execute(select(WatchQueue).where(
            WatchQueue.id == queue_id, WatchQueue.user_id == user_id,
        ))
        q = res.scalar_one_or_none()
        if q is None:
            return False
        await self.s.execute(delete(WatchQueue).where(WatchQueue.id == queue_id))
        await self.s.commit()
        return True

    async def items(self, user_id: uuid.UUID, queue_id: uuid.UUID) -> list[uuid.UUID]:
        res = await self.s.execute(select(WatchQueue).where(
            WatchQueue.id == queue_id, WatchQueue.user_id == user_id,
        ))
        if res.scalar_one_or_none() is None:
            return []
        res = await self.s.execute(
            select(QueueItem.content_id).where(QueueItem.queue_id == queue_id).order_by(QueueItem.position, QueueItem.added_at)
        )
        return list(res.scalars().all())

    async def add_item(self, user_id: uuid.UUID, queue_id: uuid.UUID, content_id: uuid.UUID) -> bool:
        res = await self.s.execute(select(WatchQueue).where(
            WatchQueue.id == queue_id, WatchQueue.user_id == user_id,
        ))
        if res.scalar_one_or_none() is None:
            return False
        existing = await self.s.execute(select(QueueItem).where(
            QueueItem.queue_id == queue_id, QueueItem.content_id == content_id,
        ))
        if existing.scalar_one_or_none() is None:
            self.s.add(QueueItem(queue_id=queue_id, content_id=content_id))
            await self.s.commit()
        return True

    async def remove_item(self, user_id: uuid.UUID, queue_id: uuid.UUID, content_id: uuid.UUID) -> bool:
        res = await self.s.execute(select(WatchQueue).where(
            WatchQueue.id == queue_id, WatchQueue.user_id == user_id,
        ))
        if res.scalar_one_or_none() is None:
            return False
        await self.s.execute(delete(QueueItem).where(
            QueueItem.queue_id == queue_id, QueueItem.content_id == content_id,
        ))
        await self.s.commit()
        return True
