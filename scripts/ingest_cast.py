"""Populate persons + credits from TVMaze cast endpoint for series we have.

Usage:
    python scripts/ingest_cast.py
"""
import os
import time
import uuid

import httpx
from loguru import logger
from sqlalchemy import create_engine, text


def main():
    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    eng = create_engine(url)
    with eng.connect() as c:
        rows = c.execute(text("""SELECT id, title FROM content WHERE type='series' LIMIT 60""")).mappings().all()
    persons_seen: dict[str, str] = {}
    credits_added = 0
    with httpx.Client() as client, eng.begin() as c:
        for r in rows:
            try:
                rr = client.get("https://api.tvmaze.com/search/shows",
                                params={"q": r["title"]}, timeout=8)
                hits = rr.json() if rr.status_code == 200 else []
                if not hits:
                    continue
                show_id = hits[0]["show"]["id"]
                cr = client.get(f"https://api.tvmaze.com/shows/{show_id}/cast", timeout=8)
                if cr.status_code != 200:
                    continue
                for i, cast_entry in enumerate(cr.json()[:8]):
                    person = cast_entry.get("person") or {}
                    character = cast_entry.get("character") or {}
                    name = person.get("name")
                    if not name:
                        continue
                    if name in persons_seen:
                        pid = persons_seen[name]
                    else:
                        pid = str(uuid.uuid4())
                        photo = (person.get("image") or {}).get("medium", "")
                        try:
                            c.execute(text("""
                                INSERT INTO persons (id, name, photo_url)
                                VALUES (:i, :n, :p)
                                ON CONFLICT (name) DO UPDATE SET photo_url=EXCLUDED.photo_url
                                RETURNING id
                            """), {"i": pid, "n": name, "p": photo})
                        except Exception:
                            continue
                        persons_seen[name] = pid
                    c.execute(text("""
                        INSERT INTO credits (content_id, person_id, role, character, position)
                        VALUES (:c, :p, 'actor', :ch, :pos)
                        ON CONFLICT DO NOTHING
                    """), {"c": str(r["id"]), "p": pid,
                           "ch": (character.get("name") or "")[:255], "pos": i})
                    credits_added += 1
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"{r['title']}: {e}")
    logger.success(f"Persons={len(persons_seen)}, credits={credits_added}")


if __name__ == "__main__":
    main()
