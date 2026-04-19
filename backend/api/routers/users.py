from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from repositories.user_repo import UserRepo
from schemas.user import PreferencesIn, PreferencesOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.get("/me/preferences", response_model=PreferencesOut)
async def get_preferences(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = UserRepo(db)
    prefs = await repo.get_preferences(user.id)
    if prefs is None:
        prefs = await repo.upsert_preferences(user.id)
    return prefs


@router.put("/me/preferences", response_model=PreferencesOut)
async def update_preferences(
    body: PreferencesIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = UserRepo(db)
    return await repo.upsert_preferences(user.id, **body.model_dump())
