import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import require_admin
from models.user import User
from repositories.content_repo import ContentRepo
from schemas.content import ContentCreate, ContentOut, ContentUpdate, GenreOut
from services.content_service import ContentService

router = APIRouter(prefix="/content", tags=["content"])


def _svc(db: AsyncSession) -> ContentService:
    return ContentService(ContentRepo(db))


@router.get("", response_model=list[ContentOut])
async def list_content(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await _svc(db).list(limit=limit, offset=offset)


@router.get("/genres", response_model=list[GenreOut])
async def list_genres(db: Annotated[AsyncSession, Depends(get_db)]):
    return await _svc(db).genres()


@router.get("/{content_id}", response_model=ContentOut)
async def get_content(content_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    return await _svc(db).get(content_id)


@router.post("", response_model=ContentOut, status_code=status.HTTP_201_CREATED)
async def create_content(
    body: ContentCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await _svc(db).create(body.model_dump())


@router.patch("/{content_id}", response_model=ContentOut)
async def update_content(
    content_id: uuid.UUID,
    body: ContentUpdate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await _svc(db).update(content_id, body.model_dump(exclude_unset=True))
