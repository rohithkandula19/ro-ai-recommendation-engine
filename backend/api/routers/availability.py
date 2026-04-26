"""Where-to-watch: provider deep-links + user subscriptions.

RO does not stream licensed content. We point users to the services that do —
sourced from TMDB's /watch/providers endpoint (JustWatch data).
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.availability import ContentAvailability
from models.subscription import UserSubscription
from models.user import User

router = APIRouter(prefix="/availability", tags=["availability"])


KNOWN_PROVIDERS = [
    "Netflix", "Amazon Prime Video", "Max", "Disney Plus", "Hulu",
    "Apple TV Plus", "Peacock", "Paramount Plus", "Starz", "Showtime",
    "AMC Plus", "Crunchyroll", "Tubi TV", "Pluto TV", "Freevee",
    "YouTube", "Apple TV", "Amazon Video", "Google Play Movies", "Vudu",
]


@router.get("/providers")
async def list_known_providers():
    return {"providers": KNOWN_PROVIDERS}


@router.get("/{content_id}")
async def get_availability(
    content_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    region: str = Query("US", min_length=2, max_length=3),
):
    q = (
        select(ContentAvailability)
        .where(ContentAvailability.content_id == content_id)
        .where(ContentAvailability.region == region.upper())
    )
    rows = (await db.execute(q)).scalars().all()
    offers: dict[str, list] = {"stream": [], "rent": [], "buy": [], "free": []}
    for r in rows:
        offers.setdefault(r.offer_type, []).append({
            "provider": r.provider,
            "provider_logo": r.provider_logo,
            "deep_link": r.deep_link,
            "price": r.price,
            "currency": r.currency,
            "quality": r.quality,
        })
    return {"content_id": str(content_id), "region": region.upper(), "offers": offers}


@router.get("/me/subscriptions")
async def get_my_subscriptions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    rows = (await db.execute(
        select(UserSubscription.provider).where(UserSubscription.user_id == user.id)
    )).scalars().all()
    return {"providers": list(rows)}


@router.put("/me/subscriptions")
async def set_my_subscriptions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    providers: list[str] = Body(..., embed=True),
):
    clean = sorted({p.strip() for p in providers if p and isinstance(p, str)})
    await db.execute(delete(UserSubscription).where(UserSubscription.user_id == user.id))
    for p in clean:
        db.add(UserSubscription(user_id=user.id, provider=p))
    await db.commit()
    return {"providers": clean}


@router.post("/match")
async def match_my_services(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    content_ids: list[uuid.UUID] = Body(..., embed=True),
    region: str = Body("US", embed=True),
):
    """Given a list of content ids, return which providers (from the user's
    subscriptions) stream each one. UI uses this to badge cards or filter."""
    if not content_ids:
        return {"matches": {}}
    subs = (await db.execute(
        select(UserSubscription.provider).where(UserSubscription.user_id == user.id)
    )).scalars().all()
    if not subs:
        return {"matches": {}, "subscriptions": []}

    q = (
        select(ContentAvailability.content_id, ContentAvailability.provider)
        .where(and_(
            ContentAvailability.content_id.in_(content_ids),
            ContentAvailability.provider.in_(list(subs)),
            ContentAvailability.offer_type.in_(["stream", "free"]),
            ContentAvailability.region == region.upper(),
        ))
    )
    rows = (await db.execute(q)).all()
    matches: dict[str, list[str]] = {}
    for cid, provider in rows:
        matches.setdefault(str(cid), []).append(provider)
    return {"matches": matches, "subscriptions": sorted(subs)}
