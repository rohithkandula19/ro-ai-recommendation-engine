import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserPreferences


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        res = await self.session.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str, display_name: str) -> User:
        user = User(email=email, hashed_password=hashed_password, display_name=display_name)
        self.session.add(user)
        await self.session.flush()
        prefs = UserPreferences(user_id=user.id)
        self.session.add(prefs)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_last_active(self, user_id: uuid.UUID) -> None:
        from sqlalchemy import update
        from datetime import datetime, timezone
        await self.session.execute(
            update(User).where(User.id == user_id).values(last_active_at=datetime.now(timezone.utc))
        )
        await self.session.commit()

    async def get_preferences(self, user_id: uuid.UUID) -> UserPreferences | None:
        res = await self.session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
        return res.scalar_one_or_none()

    async def upsert_preferences(self, user_id: uuid.UUID, **fields) -> UserPreferences:
        prefs = await self.get_preferences(user_id)
        if prefs is None:
            prefs = UserPreferences(user_id=user_id, **fields)
            self.session.add(prefs)
        else:
            for k, v in fields.items():
                setattr(prefs, k, v)
        await self.session.commit()
        await self.session.refresh(prefs)
        return prefs
