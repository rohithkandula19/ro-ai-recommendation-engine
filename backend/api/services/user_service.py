import uuid
from fastapi import HTTPException, status

from core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from core.config import settings
from repositories.user_repo import UserRepo
from services.cache_service import CacheService


class UserService:
    def __init__(self, user_repo: UserRepo, cache: CacheService):
        self.user_repo = user_repo
        self.cache = cache

    async def register(self, email: str, password: str, display_name: str) -> tuple[uuid.UUID, str, str]:
        existing = await self.user_repo.get_by_email(email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = await self.user_repo.create(email=email, hashed_password=hash_password(password), display_name=display_name)
        access = create_access_token(str(user.id), user.is_admin)
        refresh = create_refresh_token(str(user.id))
        refresh_payload = decode_token(refresh)
        if refresh_payload:
            await self.cache.store_refresh_token(str(user.id), refresh_payload["jti"], settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return user.id, access, refresh

    async def login(self, email: str, password: str) -> tuple[str, str, int]:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        access = create_access_token(str(user.id), user.is_admin)
        refresh = create_refresh_token(str(user.id))
        refresh_payload = decode_token(refresh)
        if refresh_payload:
            await self.cache.store_refresh_token(str(user.id), refresh_payload["jti"], settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.update_last_active(user.id)
        return access, refresh, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def request_password_reset(self, email: str) -> str | None:
        import secrets
        from core.email import send_password_reset
        user = await self.user_repo.get_by_email(email)
        if user is None:
            return None
        token = secrets.token_urlsafe(32)
        await self.cache.redis.set(f"pwreset:{token}", str(user.id), ex=30 * 60)
        sent = await send_password_reset(email, token)
        from loguru import logger
        if not sent:
            logger.info(f"Password reset (dev, no provider) for {email}: {token}")
        return token

    async def confirm_password_reset(self, token: str, new_password: str) -> bool:
        user_id = await self.cache.redis.get(f"pwreset:{token}")
        if not user_id:
            return False
        import uuid as _uuid
        user = await self.user_repo.get_by_id(_uuid.UUID(user_id))
        if user is None:
            return False
        user.hashed_password = hash_password(new_password)
        await self.user_repo.session.commit()
        await self.cache.redis.delete(f"pwreset:{token}")
        # Revoke all refresh tokens for this user
        async for key in self.cache.redis.scan_iter(match=f"refresh:{user_id}:*", count=100):
            await self.cache.redis.delete(key)
        return True

    async def refresh(self, refresh_token: str) -> tuple[str, str, int]:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = payload["sub"]
        jti = payload["jti"]
        if not await self.cache.is_refresh_valid(user_id, jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        await self.cache.revoke_refresh(user_id, jti)
        new_access = create_access_token(user_id, user.is_admin)
        new_refresh = create_refresh_token(user_id)
        new_payload = decode_token(new_refresh)
        if new_payload:
            await self.cache.store_refresh_token(user_id, new_payload["jti"], settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return new_access, new_refresh, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
