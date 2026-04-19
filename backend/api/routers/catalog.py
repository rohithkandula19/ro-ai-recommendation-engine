"""Catalog routes: /movies, /series, /collections — filterable lists over real content."""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.content import Content, Genre
from models.user import User

router = APIRouter(tags=["catalog"])


SORTS = {
    "popular": Content.popularity_score.desc(),
    "newest": Content.release_year.desc().nullslast(),
    "oldest": Content.release_year.asc().nullslast(),
    "title": Content.title.asc(),
    "completion": Content.completion_rate.desc(),
}


def _to_json(c: Content) -> dict:
    return {
        "id": str(c.id),
        "title": c.title,
        "type": c.type,
        "release_year": c.release_year,
        "duration_seconds": c.duration_seconds,
        "thumbnail_url": c.thumbnail_url,
        "popularity_score": float(c.popularity_score or 0),
        "completion_rate": float(c.completion_rate or 0),
        "maturity_rating": c.maturity_rating,
        "genre_ids": list(c.genre_ids or []),
    }


async def _list(
    db: AsyncSession, *, type_filter: str | None, genre: int | None,
    min_year: int | None, max_year: int | None,
    max_minutes: int | None, sort: str, limit: int, offset: int,
) -> dict:
    stmt = select(Content).where(Content.is_active == True)
    if type_filter:
        stmt = stmt.where(Content.type == type_filter)
    if genre is not None:
        stmt = stmt.where(Content.genre_ids.any(genre))
    if min_year is not None:
        stmt = stmt.where(Content.release_year >= min_year)
    if max_year is not None:
        stmt = stmt.where(Content.release_year <= max_year)
    if max_minutes is not None:
        stmt = stmt.where(Content.duration_seconds <= max_minutes * 60)
    stmt = stmt.order_by(SORTS.get(sort, Content.popularity_score.desc())).limit(limit).offset(offset)
    items = list((await db.execute(stmt)).scalars().all())

    count_stmt = select(func.count(Content.id)).where(Content.is_active == True)
    if type_filter:
        count_stmt = count_stmt.where(Content.type == type_filter)
    total = (await db.execute(count_stmt)).scalar_one()

    return {
        "total": int(total),
        "limit": limit, "offset": offset,
        "items": [_to_json(c) for c in items],
    }


@router.get("/movies")
async def movies(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    genre: int | None = Query(None),
    min_year: int | None = Query(None),
    max_year: int | None = Query(None),
    max_minutes: int | None = Query(None, ge=5, le=600),
    sort: str = Query("popular", pattern="^(popular|newest|oldest|title|completion)$"),
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await _list(db, type_filter="movie", genre=genre, min_year=min_year, max_year=max_year,
                       max_minutes=max_minutes, sort=sort, limit=limit, offset=offset)


@router.get("/series")
async def series(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    genre: int | None = Query(None),
    min_year: int | None = Query(None),
    max_year: int | None = Query(None),
    sort: str = Query("popular", pattern="^(popular|newest|oldest|title|completion)$"),
    limit: int = Query(40, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await _list(db, type_filter="series", genre=genre, min_year=min_year, max_year=max_year,
                       max_minutes=None, sort=sort, limit=limit, offset=offset)


COLLECTIONS = {
    "top-10": {
        "title": "Top 10 Right Now",
        "filter": lambda q: q.order_by(Content.popularity_score.desc()).limit(10),
    },
    "hidden-gems": {
        "title": "Hidden Gems",
        "filter": lambda q: q.where(Content.popularity_score < 0.3, Content.completion_rate > 0.6)
                             .order_by(Content.completion_rate.desc()).limit(20),
    },
    "short-and-sweet": {
        "title": "Under 90 Minutes",
        "filter": lambda q: q.where(Content.type == "movie", Content.duration_seconds < 90 * 60)
                             .order_by(Content.popularity_score.desc()).limit(20),
    },
    "marathon-worthy": {
        "title": "Marathon-Worthy",
        "filter": lambda q: q.where(Content.type == "series", Content.completion_rate > 0.55)
                             .order_by(Content.popularity_score.desc()).limit(20),
    },
    "dark-and-tense": {
        "title": "Dark & Tense",
        "filter": lambda q: q.where(Content.mood_chill_tense > 0.7)
                             .order_by(Content.popularity_score.desc()).limit(20),
    },
    "light-and-funny": {
        "title": "Light & Funny",
        "filter": lambda q: q.where(Content.vibe_humor > 0.7, Content.mood_chill_tense < 0.4)
                             .order_by(Content.popularity_score.desc()).limit(20),
    },
    "mind-benders": {
        "title": "Mind-Benders",
        "filter": lambda q: q.where(Content.vibe_complexity > 0.75)
                             .order_by(Content.popularity_score.desc()).limit(20),
    },
    "this-year": {
        "title": f"Released in {datetime.now().year}",
        "filter": lambda q: q.where(Content.release_year >= datetime.now().year - 1)
                             .order_by(Content.release_year.desc(), Content.popularity_score.desc()).limit(20),
    },
}


@router.get("/collections")
async def list_collections(_: Annotated[User, Depends(get_current_user)]):
    return {"items": [{"slug": k, "title": v["title"]} for k, v in COLLECTIONS.items()]}


@router.get("/collections/{slug}")
async def collection_items(
    slug: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    col = COLLECTIONS.get(slug)
    if col is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Collection not found")
    q = select(Content).where(Content.is_active == True)
    q = col["filter"](q)
    items = list((await db.execute(q)).scalars().all())
    return {"slug": slug, "title": col["title"], "items": [_to_json(c) for c in items]}
