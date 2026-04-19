from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from repositories.content_repo import ContentRepo
from schemas.content import SearchResponse, SearchResultItem
from services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(min_length=1, max_length=255),
    limit: int = Query(20, ge=1, le=50),
):
    svc = SearchService(ContentRepo(db))
    pairs = await svc.search(q, limit=limit)
    results = [
        SearchResultItem(
            id=c.id, title=c.title, type=c.type,
            relevance_score=score, thumbnail_url=c.thumbnail_url,
        )
        for c, score in pairs
    ]
    return SearchResponse(query=q, results=results)
