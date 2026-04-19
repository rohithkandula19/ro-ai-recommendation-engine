"""Integrations: Spotify soundtrack embed + ElevenLabs voice TTS."""
import os
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from core.database import get_db
from middleware.auth_middleware import get_current_user
from models.user import User

router = APIRouter(tags=["integrations"])


# ─── Spotify — soundtrack lookup ─────────────────────────
SPOTIFY_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
_spotify_token: dict = {"value": None, "exp": 0}


async def _spotify_token_get() -> str | None:
    import time
    if _spotify_token["value"] and time.time() < _spotify_token["exp"]:
        return _spotify_token["value"]
    if not SPOTIFY_ID or not SPOTIFY_SECRET:
        return None
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.post("https://accounts.spotify.com/api/token",
                              data={"grant_type": "client_credentials"},
                              auth=(SPOTIFY_ID, SPOTIFY_SECRET))
        if r.status_code != 200:
            return None
        data = r.json()
        _spotify_token["value"] = data["access_token"]
        _spotify_token["exp"] = time.time() + data.get("expires_in", 3600) - 60
        return _spotify_token["value"]


@router.get("/integrations/spotify/soundtrack")
async def soundtrack(
    content_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = (await db.execute(text(
        "SELECT title, release_year FROM content WHERE id=:c"
    ), {"c": str(content_id)})).first()
    if not row:
        raise HTTPException(status_code=404)
    title, year = row
    tok = await _spotify_token_get()
    if not tok:
        return {"enabled": False,
                "message": "Set SPOTIFY_CLIENT_ID + SPOTIFY_CLIENT_SECRET in .env to enable."}
    q = f"{title} soundtrack"
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get("https://api.spotify.com/v1/search",
                             params={"q": q, "type": "album", "limit": 1},
                             headers={"Authorization": f"Bearer {tok}"})
        if r.status_code != 200:
            return {"results": []}
        albums = r.json().get("albums", {}).get("items", [])
        if not albums:
            return {"results": []}
        album = albums[0]
        return {
            "enabled": True,
            "album": {
                "id": album["id"],
                "name": album["name"],
                "image": album["images"][0]["url"] if album.get("images") else None,
                "external_url": album["external_urls"]["spotify"],
                "embed_url": f"https://open.spotify.com/embed/album/{album['id']}",
            },
        }


# ─── ElevenLabs TTS proxy ────────────────────────────────
class TTSIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice: str = Field(default="Rachel")


@router.post("/integrations/tts")
async def tts(
    body: TTSIn,
    _: Annotated[User, Depends(get_current_user)],
):
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise HTTPException(status_code=501,
                            detail="Voice TTS needs ELEVENLABS_API_KEY (fall back to browser SpeechSynthesis)")
    # Rachel voice_id (public premade)
    voice_id = {"Rachel": "21m00Tcm4TlvDq8ikWAM", "Adam": "pNInz6obpgDQGcFmaJgB"}.get(body.voice, "21m00Tcm4TlvDq8ikWAM")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": key, "Content-Type": "application/json", "accept": "audio/mpeg"},
            json={"text": body.text[:4800], "model_id": "eleven_turbo_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="tts failed")

    async def iter_audio():
        yield r.content
    return StreamingResponse(iter_audio(), media_type="audio/mpeg")
