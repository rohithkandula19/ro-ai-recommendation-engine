import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.content import Content, Genre


class ContentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, content_id: uuid.UUID) -> Content | None:
        res = await self.session.execute(select(Content).where(Content.id == content_id))
        return res.scalar_one_or_none()

    async def list_active(self, limit: int = 50, offset: int = 0) -> list[Content]:
        res = await self.session.execute(
            select(Content).where(Content.is_active == True)
            .order_by(Content.popularity_score.desc()).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    async def get_many(self, ids: list[uuid.UUID]) -> list[Content]:
        if not ids:
            return []
        res = await self.session.execute(select(Content).where(Content.id.in_(ids)))
        items = list(res.scalars().all())
        order = {cid: i for i, cid in enumerate(ids)}
        return sorted(items, key=lambda c: order.get(c.id, 1_000_000))

    async def search(self, query: str, limit: int = 20) -> list[tuple[Content, float]]:
        q = f"%{query.lower()}%"
        res = await self.session.execute(
            select(Content).where(
                Content.is_active == True,
                or_(func.lower(Content.title).like(q), func.lower(Content.description).like(q)),
            ).limit(limit)
        )
        items = list(res.scalars().all())
        scored = []
        for c in items:
            relevance = 1.0 if c.title and query.lower() in c.title.lower() else 0.5
            scored.append((c, relevance))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored

    async def create(self, **fields) -> Content:
        c = Content(**fields)
        self.session.add(c)
        await self.session.commit()
        await self.session.refresh(c)
        return c

    async def update(self, content_id: uuid.UUID, **fields) -> Content | None:
        c = await self.get_by_id(content_id)
        if c is None:
            return None
        for k, v in fields.items():
            if v is not None:
                setattr(c, k, v)
        await self.session.commit()
        await self.session.refresh(c)
        return c

    async def list_genres(self) -> list[Genre]:
        res = await self.session.execute(select(Genre).order_by(Genre.name))
        return list(res.scalars().all())

    async def new_releases(self, limit: int = 20) -> list[Content]:
        res = await self.session.execute(
            select(Content).where(Content.is_active == True)
            .order_by(Content.created_at.desc()).limit(limit)
        )
        return list(res.scalars().all())

    async def trending(self, limit: int = 20) -> list[Content]:
        res = await self.session.execute(
            select(Content).where(Content.is_active == True)
            .order_by(Content.popularity_score.desc()).limit(limit)
        )
        return list(res.scalars().all())
