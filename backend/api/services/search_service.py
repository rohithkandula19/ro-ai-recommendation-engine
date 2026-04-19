from repositories.content_repo import ContentRepo


class SearchService:
    def __init__(self, repo: ContentRepo):
        self.repo = repo

    async def search(self, query: str, limit: int = 20):
        q = (query or "").strip()
        if not q:
            return []
        return await self.repo.search(q, limit=limit)
