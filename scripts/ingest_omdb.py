"""Enrich real_content.json + tvmaze_ingested.json with OMDb data.

For each title, look up by (title, year) and pull real:
  - IMDb poster URL
  - IMDb rating, rotten tomatoes, metacritic
  - Awards text
  - Plot (fuller than our seed)
  - Runtime (authoritative)

Writes an omdb_enriched.json merged catalog.

Usage:
    OMDB_API_KEY=xxx python scripts/ingest_omdb.py --output scripts/omdb_enriched.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import httpx
from loguru import logger


OMDB_KEY = os.getenv("OMDB_API_KEY")
OMDB = "https://www.omdbapi.com/"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text()).get("titles", [])
    except Exception as e:
        logger.warning(f"load {path}: {e}")
        return []


def _lookup(client: httpx.Client, title: str, year: int | None) -> dict | None:
    params = {"apikey": OMDB_KEY, "t": title, "plot": "short"}
    if year:
        params["y"] = str(year)
    try:
        r = client.get(OMDB, params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("Response") != "True":
            return None
        return data
    except Exception as e:
        logger.warning(f"omdb err for {title}: {e}")
        return None


def _enrich(entry: dict, omdb: dict) -> dict:
    poster = omdb.get("Poster") or ""
    if poster == "N/A":
        poster = entry.get("poster", "")
    runtime = entry.get("runtime_min")
    rt = omdb.get("Runtime", "")
    if rt and rt.endswith(" min"):
        try:
            runtime = int(rt[:-4])
        except ValueError:
            pass
    ratings = omdb.get("Ratings") or []
    rating_map = {r.get("Source"): r.get("Value") for r in ratings}
    cast = entry.get("cast") or []
    actors = (omdb.get("Actors") or "").split(",") if omdb.get("Actors") else []
    if actors:
        cast = [a.strip() for a in actors if a.strip()][:5]

    return {
        **entry,
        "poster": poster if poster.startswith("http") else entry.get("poster", ""),
        "runtime_min": runtime,
        "description": omdb.get("Plot") if omdb.get("Plot") and omdb["Plot"] != "N/A" else entry.get("description", ""),
        "director": omdb.get("Director") if omdb.get("Director") and omdb["Director"] != "N/A" else entry.get("director", ""),
        "cast": cast,
        "rating": omdb.get("Rated") if omdb.get("Rated") and omdb["Rated"] != "N/A" else entry.get("rating", ""),
        "imdb_rating": omdb.get("imdbRating") if omdb.get("imdbRating") != "N/A" else None,
        "imdb_id": omdb.get("imdbID"),
        "rt_rating": rating_map.get("Rotten Tomatoes"),
        "metascore": omdb.get("Metascore") if omdb.get("Metascore") != "N/A" else None,
        "awards": omdb.get("Awards") if omdb.get("Awards") and omdb["Awards"] != "N/A" else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(Path(__file__).parent / "omdb_enriched.json"))
    parser.add_argument("--max", type=int, default=400, help="cap lookups (free tier = 1000/day)")
    args = parser.parse_args()
    if not OMDB_KEY:
        logger.error("OMDB_API_KEY env var not set")
        return

    sources = [
        Path(__file__).parent / "real_content.json",
        Path(__file__).parent / "tvmaze_ingested.json",
    ]
    catalog: list[dict] = []
    for p in sources:
        catalog.extend(_load(p))

    seen = set()
    unique = []
    for t in catalog:
        key = (t.get("title", "").lower(), t.get("year"))
        if key in seen or not t.get("title"):
            continue
        seen.add(key)
        unique.append(t)

    logger.info(f"enriching up to {min(args.max, len(unique))} of {len(unique)} titles")

    enriched_count = 0
    skipped = 0
    with httpx.Client() as client:
        for i, entry in enumerate(unique):
            if i >= args.max:
                break
            omdb = _lookup(client, entry["title"], entry.get("year"))
            if omdb:
                unique[i] = _enrich(entry, omdb)
                enriched_count += 1
            else:
                skipped += 1
            if (i + 1) % 25 == 0:
                logger.info(f"processed {i+1}: enriched={enriched_count} skipped={skipped}")
            time.sleep(0.08)

    all_genres = sorted({g for t in unique for g in (t.get("genres") or [])})
    Path(args.output).write_text(json.dumps({"genres": all_genres, "titles": unique}, indent=2))
    logger.success(f"Wrote {len(unique)} titles ({enriched_count} OMDb-enriched) → {args.output}")


if __name__ == "__main__":
    main()
