"""Multi-step agent: chat that can call structured tools.

The LLM returns JSON with an `actions` list the frontend auto-executes.
"""
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm import get_llm
from middleware.auth_middleware import get_current_user
from models.user import User

router = APIRouter(tags=["agent"])


class AgentIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)


@router.post("/chat/agent")
async def agent(
    body: AgentIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return a reply + an array of typed actions the frontend can execute."""
    llm = get_llm()
    if not llm.enabled:
        return {"reply": "LLM disabled; add an API key.", "actions": []}
    cands = (await db.execute(text("""
        SELECT id::text, title, release_year, type FROM content
        WHERE is_active = true ORDER BY popularity_score DESC LIMIT 30
    """))).mappings().all()
    catalog = [dict(c) for c in cands]
    system = (
        "You are an action-planning recommender. Given a user's message and a catalog, "
        "return JSON: {\"reply\": str, \"actions\": [{\"kind\": str, \"content_id\": str, \"label\": str}]}. "
        "kind is one of: play, add_to_list, rate, mark_watched, view_details. "
        "Only reference content_ids from the catalog. Max 4 actions."
    )
    parsed = await llm.complete_json(
        system=system,
        user=json.dumps({"message": body.message, "catalog": catalog}),
        max_tokens=400, temperature=0.3,
    )
    if not parsed:
        return {"reply": "Sorry, I couldn't parse that.", "actions": []}
    # validate content ids
    valid_ids = {c["id"] for c in catalog}
    parsed["actions"] = [a for a in parsed.get("actions", [])
                         if isinstance(a, dict) and a.get("content_id") in valid_ids]
    return parsed


class ImageSearchIn(BaseModel):
    description: str = Field(max_length=500)


@router.post("/search/image-vibe")
async def image_vibe(
    body: ImageSearchIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stub: takes an image description (frontend uses CLIP-like embedding or
    LLM caption) and returns similar-vibe titles."""
    import httpx
    from core.config import settings
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{settings.ML_SERVICE_URL}/ml/semantic-search",
                                  json={"query": body.description, "k": 12})
            ids = r.json().get("ids", []) if r.status_code == 200 else []
    except Exception:
        ids = []
    if not ids:
        return {"results": []}
    rows = (await db.execute(text("""
        SELECT id, title, thumbnail_url, release_year FROM content WHERE id = ANY(:ids::uuid[])
    """), {"ids": ids})).mappings().all()
    return {"results": [{"id": str(r["id"]), "title": r["title"],
                         "thumbnail_url": r["thumbnail_url"], "release_year": r["release_year"]}
                        for r in rows]}


@router.post("/chat/voice-transcribe")
async def voice_transcribe(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    """Server-side voice transcription fallback (frontend uses WebSpeech primarily).
    If OPENAI_API_KEY is set, forwards to Whisper; otherwise returns 501."""
    import os
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=501, detail="Voice transcribe needs OPENAI_API_KEY")
    import httpx
    content = await file.read()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post("https://api.openai.com/v1/audio/transcriptions",
                              headers={"Authorization": f"Bearer {key}"},
                              files={"file": (file.filename, content, file.content_type)},
                              data={"model": "whisper-1"})
        if r.status_code == 200:
            return {"text": r.json().get("text", "")}
        raise HTTPException(status_code=502, detail="transcription failed")
