import uuid
from fastapi import HTTPException, status

from repositories.content_repo import ContentRepo


class ContentService:
    def __init__(self, repo: ContentRepo):
        self.repo = repo

    async def get(self, content_id: uuid.UUID):
        c = await self.repo.get_by_id(content_id)
        if c is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        return c

    async def list(self, limit: int, offset: int):
        return await self.repo.list_active(limit=limit, offset=offset)

    async def create(self, data: dict):
        return await self.repo.create(**data)

    async def update(self, content_id: uuid.UUID, data: dict):
        updated = await self.repo.update(content_id, **data)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        return updated

    async def genres(self):
        return await self.repo.list_genres()
