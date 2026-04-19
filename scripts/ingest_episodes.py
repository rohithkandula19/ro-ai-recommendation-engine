"""Hydrate episodes table from TVMaze for all content with tvmaze_id set on metadata.

Usage:
    python scripts/ingest_episodes.py
"""
import json
import os
import time
from pathlib import Path

import httpx
from loguru import logger
from sqlalchemy import create_engine, text


def main():
    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    eng = create_engine(url)
    # Find series in our DB that we have TVMaze hints for via the trakt_ingested merge (ids)
    with eng.connect() as c:
        rows = c.execute(text("""
            SELECT id, title FROM content WHERE type='series' LIMIT 80
        """)).mappings().all()
    inserted = 0
    with httpx.Client() as client:
        for r in rows:
            try:
                rr = client.get("https://api.tvmaze.com/search/shows",
                                params={"q": r["title"]}, timeout=8)
                hits = rr.json() if rr.status_code == 200 else []
                if not hits:
                    continue
                show_id = hits[0]["show"]["id"]
                er = client.get(f"https://api.tvmaze.com/shows/{show_id}/episodes", timeout=10)
                if er.status_code != 200:
                    continue
                # commit per-show so a bad row doesn't poison the whole run
                with eng.begin() as c:
                    for ep in er.json():
                        try:
                            c.execute(text("""
                                INSERT INTO episodes (content_id, season, number, title, description,
                                                      duration_seconds, aired_at, thumbnail_url)
                                VALUES (:cid, :s, :n, :t, :d, :dur, :a, :th)
                                ON CONFLICT (content_id, season, number) DO NOTHING
                            """), {
                                "cid": str(r["id"]), "s": ep.get("season", 0), "n": ep.get("number", 0),
                                "t": (ep.get("name") or "")[:255],
                                "d": ((ep.get("summary") or "").replace("<p>", "").replace("</p>", ""))[:2000],
                                "dur": (ep.get("runtime") or 0) * 60,
                                "a": ep.get("airdate"),
                                "th": ((ep.get("image") or {}).get("medium", "") or "")[:500],
                            })
                            inserted += 1
                        except Exception:
                            continue
                time.sleep(0.15)
            except Exception as e:
                logger.warning(f"{r['title']}: {e}")
    logger.success(f"Inserted {inserted} episodes")


if __name__ == "__main__":
    main()
