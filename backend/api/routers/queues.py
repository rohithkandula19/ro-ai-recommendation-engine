import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from services.queue_service import QueueService

router = APIRouter(prefix="/users/me/queues", tags=["queues"])


class QueueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    icon: str | None = Field(default=None, max_length=20)


class QueueOut(BaseModel):
    id: str
    name: str
    icon: str | None = None
    count: int


@router.get("", response_model=list[QueueOut])
async def list_queues(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    return await QueueService(db).list(user.id)


@router.post("", response_model=QueueOut, status_code=status.HTTP_201_CREATED)
async def create_queue(body: QueueCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    svc = QueueService(db)
    q = await svc.create(user.id, body.name, body.icon)
    return {"id": str(q.id), "name": q.name, "icon": q.icon, "count": 0}


@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_queue(queue_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    svc = QueueService(db)
    if not await svc.delete(user.id, queue_id):
        raise HTTPException(status_code=404, detail="Queue not found")


@router.get("/{queue_id}/items")
async def queue_items(queue_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    ids = await QueueService(db).items(user.id, queue_id)
    return {"queue_id": str(queue_id), "content_ids": [str(i) for i in ids]}


@router.post("/{queue_id}/items/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_item(queue_id: uuid.UUID, content_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    if not await QueueService(db).add_item(user.id, queue_id, content_id):
        raise HTTPException(status_code=404, detail="Queue not found")


@router.delete("/{queue_id}/items/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(queue_id: uuid.UUID, content_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    if not await QueueService(db).remove_item(user.id, queue_id, content_id):
        raise HTTPException(status_code=404, detail="Queue not found")
