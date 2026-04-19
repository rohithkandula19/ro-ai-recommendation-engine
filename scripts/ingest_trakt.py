"""Ingest from Trakt — real movies & TV with YouTube trailer URLs, IMDB ratings,
and TMDB image paths (TMDB poster CDN is public).

Endpoints used:
  /movies/trending        real-time trending
  /movies/popular         all-time popular
  /shows/trending
  /shows/popular
  /movies/recommended/weekly  (requires auth OAuth — skipped)

Poster images: Trakt returns tmdb_id. We use tmdb public image CDN if a
TMDB_IMG_TOKEN isn't set, else fall back to a deterministic placeholder.
Trakt itself does NOT return image URLs — you need TMDB for that.

Usage:
    TRAKT_CLIENT_ID=xxx python scripts/ingest_trakt.py --pages 5 --output scripts/trakt_ingested.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import httpx
from loguru import logger


TRAKT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_BASE = "https://api.trakt.tv"
TMDB_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"


def _headers() -> dict:
    return {
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_ID,
        "Content-Type": "application/json",
    }


def _tmdb_poster(client: httpx.Client, tmdb_id: int, kind: str) -> str:
    """Return a TMDB poster_path if TMDB_API_KEY is set, else empty string."""
    if not TMDB_KEY or not tmdb_id:
        return ""
    path = "movie" if kind == "movie" else "tv"
    try:
        r = client.get(f"{TMDB_BASE}/{path}/{tmdb_id}", params={"api_key": TMDB_KEY}, timeout=6)
        if r.status_code == 200:
            p = r.json().get("poster_path") or ""
            return p or ""
    except Exception:
        pass
    return ""


def _fetch_list(client: httpx.Client, path: str, pages: int, kind: str, wrap_key: str | None) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        try:
            r = client.get(f"{TRAKT_BASE}{path}", headers=_headers(),
                           params={"page": page, "limit": 20, "extended": "full"}, timeout=15)
            if r.status_code != 200:
                logger.warning(f"trakt {path} page {page}: {r.status_code}")
                break
            items = r.json()
        except Exception as e:
            logger.warning(f"trakt {path} err: {e}")
            break
        for item in items:
            if wrap_key:
                item = item.get(wrap_key) or {}
            if not item:
                continue
            out.append(_normalize(client, item, kind))
            time.sleep(0.04)
        logger.info(f"{path} page {page}: total={len(out)}")
    return out


def _normalize(client: httpx.Client, item: dict, kind: str) -> dict:
    ids = item.get("ids", {}) or {}
    tmdb_id = ids.get("tmdb")
    poster_path = _tmdb_poster(client, tmdb_id, kind) if tmdb_id else ""
    trailer = item.get("trailer") or ""
    runtime = item.get("runtime") or 0
    if kind == "series" and runtime == 0:
        runtime = 45
    genres = [g.title() if isinstance(g, str) else "" for g in (item.get("genres") or [])]

    return {
        "title": item.get("title"),
        "type": kind,
        "year": item.get("year"),
        "runtime_min": runtime,
        "genres": [g for g in genres if g],
        "rating": item.get("certification") or ("TV-14" if kind == "series" else "PG-13"),
        "director": "",
        "cast": [],
        "tmdb_id": tmdb_id,
        "imdb_id": ids.get("imdb"),
        "trakt_id": ids.get("trakt"),
        "poster": poster_path,
        "trailer_url": trailer,
        "description": (item.get("overview") or item.get("tagline") or "").strip(),
        "trakt_rating": item.get("rating"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=10, help="20 titles per page per endpoint")
    parser.add_argument("--output", default=str(Path(__file__).parent / "trakt_ingested.json"))
    args = parser.parse_args()
    if not TRAKT_ID:
        logger.error("TRAKT_CLIENT_ID not set")
        return

    with httpx.Client() as client:
        movies_pop = _fetch_list(client, "/movies/popular", args.pages, "movie", None)
        movies_trending = _fetch_list(client, "/movies/trending", max(2, args.pages // 2), "movie", "movie")
        shows_pop = _fetch_list(client, "/shows/popular", args.pages, "series", None)
        shows_trending = _fetch_list(client, "/shows/trending", max(2, args.pages // 2), "series", "show")

    all_items = movies_pop + movies_trending + shows_pop + shows_trending
    seen = set()
    unique = []
    for t in all_items:
        key = (t.get("title", "").lower(), t.get("year"))
        if not t.get("title") or key in seen:
            continue
        seen.add(key)
        unique.append(t)

    genres = sorted({g for t in unique for g in (t.get("genres") or [])})
    Path(args.output).write_text(json.dumps({"genres": genres, "titles": unique}, indent=2))
    logger.success(f"Wrote {len(unique)} titles to {args.output}")


if __name__ == "__main__":
    main()
