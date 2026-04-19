"""Fetch top popular + top rated movies & TV from TMDB, return as a list of dicts
matching the real_content.json shape.

Usage:
    TMDB_API_KEY=xxx python scripts/ingest_tmdb.py --pages 20 --output scripts/tmdb_ingested.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from loguru import logger


TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_KEY = os.getenv("TMDB_API_KEY")


MOVIE_GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy",
    36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery",
    10749: "Romance", 878: "Sci-Fi", 53: "Thriller", 10752: "War", 37: "Western",
}
TV_GENRE_MAP = {
    10759: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary",
    18: "Drama", 10751: "Family", 10762: "Family", 9648: "Mystery", 10763: "News",
    10764: "Reality-TV", 10765: "Sci-Fi", 10766: "Drama", 10767: "Talk-Show",
    10768: "War", 37: "Western",
}


def _get(client: httpx.Client, path: str, **params) -> dict[str, Any]:
    params["api_key"] = TMDB_KEY
    r = client.get(f"{TMDB_BASE}{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _cert_from_release(client: httpx.Client, movie_id: int) -> str | None:
    try:
        data = _get(client, f"/movie/{movie_id}/release_dates")
        for country in data.get("results", []):
            if country.get("iso_3166_1") == "US":
                for r in country.get("release_dates", []):
                    if r.get("certification"):
                        return r["certification"]
    except Exception:
        return None
    return None


def _cert_from_tv(client: httpx.Client, tv_id: int) -> str | None:
    try:
        data = _get(client, f"/tv/{tv_id}/content_ratings")
        for country in data.get("results", []):
            if country.get("iso_3166_1") == "US":
                return country.get("rating")
    except Exception:
        return None
    return None


def _director(client: httpx.Client, kind: str, mid: int) -> str | None:
    try:
        data = _get(client, f"/{kind}/{mid}/credits")
        for crew in data.get("crew", []):
            if crew.get("job") == "Director" or (kind == "tv" and crew.get("job") == "Creator"):
                return crew.get("name")
    except Exception:
        return None
    return None


def _cast(client: httpx.Client, kind: str, mid: int, n: int = 4) -> list[str]:
    try:
        data = _get(client, f"/{kind}/{mid}/credits")
        return [c["name"] for c in data.get("cast", [])[:n] if c.get("name")]
    except Exception:
        return []


def fetch_movies(client: httpx.Client, pages: int) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        data = _get(client, "/movie/popular", page=page, language="en-US")
        for r in data.get("results", []):
            if not r.get("overview") or not r.get("release_date"):
                continue
            try:
                detail = _get(client, f"/movie/{r['id']}")
            except Exception:
                continue
            runtime = detail.get("runtime") or 0
            if runtime < 40:
                continue
            genres = [g["name"] for g in detail.get("genres", [])]
            rating = _cert_from_release(client, r["id"]) or "PG-13"
            director = _director(client, "movie", r["id"]) or ""
            cast = _cast(client, "movie", r["id"])
            out.append({
                "title": r["title"],
                "type": "movie",
                "year": int(r["release_date"][:4]) if r.get("release_date") else None,
                "runtime_min": runtime,
                "genres": genres,
                "rating": rating or "PG-13",
                "director": director,
                "cast": cast,
                "tmdb_id": r["id"],
                "poster": r.get("poster_path") or "",
                "description": r["overview"],
            })
            time.sleep(0.15)
        logger.info(f"movies page {page}: total={len(out)}")
    return out


def fetch_tv(client: httpx.Client, pages: int) -> list[dict]:
    out = []
    for page in range(1, pages + 1):
        data = _get(client, "/tv/popular", page=page, language="en-US")
        for r in data.get("results", []):
            if not r.get("overview") or not r.get("first_air_date"):
                continue
            try:
                detail = _get(client, f"/tv/{r['id']}")
            except Exception:
                continue
            ep_runtimes = detail.get("episode_run_time") or []
            runtime = ep_runtimes[0] if ep_runtimes else 45
            genres = [g["name"] for g in detail.get("genres", [])]
            rating = _cert_from_tv(client, r["id"]) or "TV-14"
            director = _director(client, "tv", r["id"]) or ""
            cast = _cast(client, "tv", r["id"])
            out.append({
                "title": r["name"],
                "type": "series",
                "year": int(r["first_air_date"][:4]) if r.get("first_air_date") else None,
                "runtime_min": runtime,
                "genres": genres,
                "rating": rating,
                "director": director,
                "cast": cast,
                "tmdb_id": r["id"],
                "poster": r.get("poster_path") or "",
                "description": r["overview"],
            })
            time.sleep(0.15)
        logger.info(f"tv page {page}: total={len(out)}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=10, help="pages per endpoint (20 results each)")
    parser.add_argument("--output", default=str(Path(__file__).parent / "tmdb_ingested.json"))
    args = parser.parse_args()
    if not TMDB_KEY:
        logger.error("TMDB_API_KEY env var not set. Get a free key at https://www.themoviedb.org/settings/api")
        sys.exit(1)

    with httpx.Client() as client:
        movies = fetch_movies(client, args.pages)
        tv = fetch_tv(client, args.pages)

    titles = movies + tv
    payload = {"genres": sorted({g for t in titles for g in t.get("genres", [])}), "titles": titles}
    Path(args.output).write_text(json.dumps(payload, indent=2))
    logger.success(f"Wrote {len(titles)} titles → {args.output}")


if __name__ == "__main__":
    main()
