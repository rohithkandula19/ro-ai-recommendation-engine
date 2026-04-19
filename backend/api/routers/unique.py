"""Unique-feature routers: taste DNA, mood, time-budget, why, co-viewer, feedback, NL search."""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User
from schemas.unique import (
    CoViewerRequest, ExplainResponse, MoodRecRequest, NLSearchRequest, NLSearchResponse,
    RankerSignal, RecFeedbackRequest, TasteDNAResponse, TimeBudgetRequest, VibeVector,
)
from schemas.recommendation import RecommendationItem, RecommendationResponse
from services.unique_service import UniqueService

router = APIRouter(tags=["unique"])


def _item(content, score: float, reason: str) -> RecommendationItem:
    return RecommendationItem(
        id=content.id, title=content.title, type=content.type,
        thumbnail_url=content.thumbnail_url,
        match_score=max(0.0, min(1.0, score)),
        reason_text=reason,
        genre_ids=list(content.genre_ids) if content.genre_ids else [],
    )


@router.get("/users/me/taste-dna", response_model=TasteDNAResponse)
async def taste_dna(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    svc = UniqueService(db)
    data = await svc.taste_dna(user.id)
    return TasteDNAResponse(user_id=user.id, dna=VibeVector(**data["dna"]), samples=data["samples"])


@router.post("/recommendations/mood", response_model=RecommendationResponse)
async def mood_recs(
    body: MoodRecRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    rows = await svc.mood_recommendations(user.id, body.chill_tense, body.light_thoughtful, body.limit)
    items = [_item(r["content"], r["score"], f"Mood match {round(r['mood_score']*100)}%") for r in rows]
    return RecommendationResponse(
        surface="mood", items=items, generated_at=datetime.now(timezone.utc), model_version="mood-v1",
    )


@router.post("/recommendations/time-budget", response_model=RecommendationResponse)
async def time_budget_recs(
    body: TimeBudgetRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    rows = await svc.time_budget_recommendations(user.id, body.minutes, body.limit, body.tolerance_pct)
    items = [
        _item(r["content"], r["score"],
              f"{round(r['completion_rate']*100)}% finish rate · {round((r['content'].duration_seconds or 0)/60)} min")
        for r in rows
    ]
    return RecommendationResponse(
        surface="time_budget", items=items, generated_at=datetime.now(timezone.utc), model_version="tb-v1",
    )


@router.get("/recommendations/explain/{content_id}", response_model=ExplainResponse)
async def explain(
    content_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    data = await svc.explain(user.id, content_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return ExplainResponse(
        content_id=data["content_id"],
        signals=[RankerSignal(**s) for s in data["signals"]],
        dominant_reason=data["dominant_reason"],
        ai_summary=data["ai_summary"],
    )


@router.post("/recommendations/co-viewer", response_model=RecommendationResponse)
async def co_viewer(
    body: CoViewerRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    if user.id not in body.user_ids:
        body.user_ids = [user.id] + body.user_ids
    rows = await svc.co_viewer(body.user_ids, body.limit)
    items = [
        _item(r["content"], r["score"],
              f"Household match {round(r['dna_match']*100)}% · agreement {round(r['agreement']*100)}%")
        for r in rows
    ]
    return RecommendationResponse(
        surface="co_viewer", items=items, generated_at=datetime.now(timezone.utc), model_version="co-viewer-v1",
    )


@router.post("/recommendations/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def record_feedback(
    body: RecFeedbackRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    await svc.record_feedback(user.id, body.content_id, body.surface, body.feedback, body.reason)


@router.get("/recommendations/anti-recs", response_model=RecommendationResponse)
async def anti_recs(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(12, ge=1, le=50),
):
    svc = UniqueService(db)
    rows = await svc.anti_recs(user.id, limit)
    items = [_item(r["content"], r["anti_score"], f"Anti-match {round(r['anti_score']*100)}% — for calibration") for r in rows]
    return RecommendationResponse(
        surface="anti_recs", items=items, generated_at=datetime.now(timezone.utc), model_version="anti-v1",
    )


@router.get("/content/{content_id}/spoiler-free")
async def spoiler_free(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    data = await svc.spoiler_free_description(content_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return data


@router.get("/content/browse/raw")
async def raw_browse(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sort: str = Query("popular", pattern="^(popular|year_desc|year_asc|title)$"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    svc = UniqueService(db)
    items = await svc.raw_browse(sort, limit, offset)
    return {
        "sort": sort,
        "personalization": "off",
        "items": [
            {"id": str(c.id), "title": c.title, "type": c.type,
             "thumbnail_url": c.thumbnail_url, "release_year": c.release_year,
             "duration_seconds": c.duration_seconds}
            for c in items
        ],
    }


@router.post("/search/nl", response_model=NLSearchResponse)
async def nl_search(
    body: NLSearchRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = UniqueService(db)
    data = await svc.nl_search(user.id, body.query, body.limit)
    items = [
        {"id": str(c.id), "title": c.title, "type": c.type, "thumbnail_url": c.thumbnail_url,
         "release_year": c.release_year, "duration_seconds": c.duration_seconds}
        for c in data["items"]
    ]
    return NLSearchResponse(
        query=body.query, parsed_filters=data["parsed_filters"],
        results=items, generated_at=datetime.now(timezone.utc),
    )
