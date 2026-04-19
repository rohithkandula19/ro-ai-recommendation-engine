from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from core.database import AsyncSessionLocal, get_db
from core.redis import get_redis
from middleware.auth_middleware import get_current_user
from models.user import User
from services.chat_service import ChatService, _finalize_buffer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatFeedbackIn(BaseModel):
    turn_index: int = Field(ge=0)
    user_message: str | None = None
    assistant_message: str = Field(min_length=1)
    feedback: int


class ChatProfileUpdate(BaseModel):
    preferred_tone: str | None = None
    preferred_reply_length: str | None = None
    custom_system_note: str | None = Field(default=None, max_length=500)


@router.get("/history")
async def history(user: Annotated[User, Depends(get_current_user)]):
    redis = await get_redis()
    async with AsyncSessionLocal() as s:
        svc = ChatService(s, redis)
        return {"turns": await svc.history(user.id)}


@router.post("/clear")
async def clear(user: Annotated[User, Depends(get_current_user)]):
    redis = await get_redis()
    async with AsyncSessionLocal() as s:
        svc = ChatService(s, redis)
        await svc.clear(user.id)
    return {"status": "ok"}


@router.post("/stream")
async def stream(
    body: ChatIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    redis = await get_redis()
    svc = ChatService(db, redis)

    async def generator():
        async for tok in svc.stream(user, body.message):
            yield tok
        await _finalize_buffer(svc, user)

    return StreamingResponse(generator(), media_type="text/plain; charset=utf-8")


@router.post("/feedback")
async def chat_feedback(
    body: ChatFeedbackIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.feedback not in (-1, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="feedback must be -1 or 1")
    redis = await get_redis()
    svc = ChatService(db, redis)
    await svc.record_feedback(user.id, body.turn_index,
                              body.user_message or "", body.assistant_message, body.feedback)
    return {"status": "ok"}


@router.get("/profile")
async def chat_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    redis = await get_redis()
    svc = ChatService(db, redis)
    p = await svc.get_or_create_profile(user.id)
    return {
        "preferred_tone": p.preferred_tone,
        "preferred_reply_length": p.preferred_reply_length,
        "custom_system_note": p.custom_system_note,
        "positive_count": p.positive_count,
        "negative_count": p.negative_count,
    }


@router.put("/profile")
async def update_chat_profile(
    body: ChatProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    redis = await get_redis()
    svc = ChatService(db, redis)
    p = await svc.get_or_create_profile(user.id)
    if body.preferred_tone is not None:
        p.preferred_tone = body.preferred_tone
    if body.preferred_reply_length is not None:
        p.preferred_reply_length = body.preferred_reply_length
    if body.custom_system_note is not None:
        p.custom_system_note = body.custom_system_note or None
    await db.commit()
    return {"status": "ok"}
