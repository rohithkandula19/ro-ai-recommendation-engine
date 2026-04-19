from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis import get_redis
from repositories.user_repo import UserRepo
from schemas.user import (
    LoginRequest, PasswordResetConfirm, PasswordResetRequest,
    RefreshRequest, RegisterRequest, RegisterResponse, TokenResponse,
)
from services.cache_service import CacheService
from services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(db: AsyncSession, redis_client) -> UserService:
    return UserService(UserRepo(db), CacheService(redis_client))


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    redis_client = await get_redis()
    svc = _service(db, redis_client)
    user_id, access, refresh = await svc.register(body.email, body.password, body.display_name)
    return RegisterResponse(user_id=user_id, access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    redis_client = await get_redis()
    svc = _service(db, redis_client)
    access, refresh, expires_in = await svc.login(body.email, body.password)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    redis_client = await get_redis()
    svc = _service(db, redis_client)
    access, refresh, expires_in = await svc.refresh(body.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/password-reset/request")
async def password_reset_request(body: PasswordResetRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    redis_client = await get_redis()
    svc = _service(db, redis_client)
    token = await svc.request_password_reset(body.email)
    # Always return 202 — do not leak whether an email exists.
    # In prod: the token is emailed, not returned. In dev: we return it for testing.
    import os
    return {
        "status": "accepted",
        "message": "If the email is registered, a reset link has been sent.",
        **({"dev_token": token} if token and os.getenv("LOG_LEVEL") == "DEBUG" else {}),
    }


@router.post("/password-reset/confirm")
async def password_reset_confirm(body: PasswordResetConfirm, db: Annotated[AsyncSession, Depends(get_db)]):
    from fastapi import HTTPException, status
    redis_client = await get_redis()
    svc = _service(db, redis_client)
    ok = await svc.confirm_password_reset(body.token, body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return {"status": "ok"}
