"""LLM-cluster content titles into franchises (Marvel, LOTR, Wizarding World, etc.).

Runs offline against OpenRouter (or whatever LLM_PROVIDER). Writes to franchises
table + updates content.franchise_id.

Usage:  python scripts/cluster_franchises.py
"""
import json
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "api"))


def main():
    try:
        from core.llm import get_llm
    except ImportError:
        print("Cannot import core.llm — run inside docker container: docker exec infra-api-1 python /tmp/cluster_franchises.py")
        sys.exit(1)

    import asyncio
    asyncio.run(_run())


async def _run():
    from core.llm import get_llm
    llm = get_llm()
    if not llm.enabled:
        print("LLM disabled — skipping")
        return

    eng = create_engine(os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine"))
    with eng.connect() as c:
        rows = c.execute(text("""
            SELECT id, title, release_year FROM content WHERE is_active = true ORDER BY popularity_score DESC LIMIT 200
        """)).mappings().all()

    titles_list = [{"id": str(r["id"]), "title": r["title"], "year": r["release_year"]} for r in rows]
    parsed = await llm.complete_json(
        system=(
            "You group movie/TV titles into FRANCHISES. A franchise is a shared universe "
            "(MCU, DCEU, Harry Potter, LOTR, Star Wars, Game of Thrones universe, etc.) "
            "OR a multi-entry series with recurring characters. Single standalone titles have no franchise."
            "\n\nReturn JSON: {\"franchises\": [{\"name\": str, \"content_ids\": [str, ...]}]}"
            "\n\nOnly group titles that clearly belong to a named franchise. Omit standalones."
        ),
        user=json.dumps(titles_list),
        max_tokens=2000, temperature=0.1,
    )
    if not parsed or "franchises" not in parsed:
        print("LLM returned no franchises")
        return

    with eng.begin() as c:
        for f in parsed["franchises"]:
            name = f.get("name", "").strip()
            ids = [i for i in f.get("content_ids", []) if i]
            if not name or not ids: continue
            r = c.execute(text("""
                INSERT INTO franchises (name) VALUES (:n)
                ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name
                RETURNING id
            """), {"n": name})
            fid = r.scalar_one()
            for cid in ids:
                try:
                    c.execute(text("UPDATE content SET franchise_id=:f WHERE id=:c"),
                              {"f": str(fid), "c": cid})
                except Exception:
                    continue
            print(f"  {name}: {len(ids)} titles")


if __name__ == "__main__":
    main()
