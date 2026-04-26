"""
Backfill TMDB poster + backdrop images for content rows that still have
picsum.photos placeholder URLs.  Searches TMDB by title + year.

Usage:
    TMDB_API_KEY=<key> python scripts/backfill_tmdb_images.py
    # or just run — key is read from secrets/.env automatically
"""
import os, sys, time, pathlib, re
import httpx
import psycopg2

# ── load env if key not already set ──────────────────────────────────────────
if not os.getenv("TMDB_API_KEY"):
    env_file = pathlib.Path(__file__).parent.parent / ".env"
    for line in env_file.read_text().splitlines():
        if line.startswith("TMDB_API_KEY="):
            os.environ["TMDB_API_KEY"] = line.split("=", 1)[1].strip()

TMDB_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"

DB_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql://recuser:recpass@localhost:5432/recengine",
)

if not TMDB_KEY:
    sys.exit("TMDB_API_KEY not set")


def search_tmdb(client: httpx.Client, title: str, year: int | None, kind: str) -> dict | None:
    endpoint = "/search/movie" if kind == "movie" else "/search/tv"
    params = {"api_key": TMDB_KEY, "query": title, "include_adult": False}
    if year:
        params["year" if kind == "movie" else "first_air_date_year"] = year
    try:
        r = client.get(f"{TMDB_BASE}{endpoint}", params=params, timeout=8)
        results = r.json().get("results", [])
        return results[0] if results else None
    except Exception:
        return None


def get_trailer_id(client: httpx.Client, tmdb_id: int, kind: str) -> str | None:
    path = "movie" if kind == "movie" else "tv"
    try:
        r = client.get(f"{TMDB_BASE}/{path}/{tmdb_id}/videos", params={"api_key": TMDB_KEY}, timeout=8)
        for v in r.json().get("results", []):
            if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                return v["key"]
    except Exception:
        pass
    return None


def run():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, type, release_year
        FROM content
        WHERE thumbnail_url LIKE '%picsum%'
        ORDER BY popularity_score DESC
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} rows with picsum placeholders")

    updated = skipped = 0
    with httpx.Client() as client:
        for row_id, title, kind, year in rows:
            result = search_tmdb(client, title, year, kind)
            if not result:
                skipped += 1
                continue

            poster = result.get("poster_path")
            backdrop = result.get("backdrop_path")
            tmdb_id = result.get("id")

            if not poster:
                skipped += 1
                continue

            trailer_id = get_trailer_id(client, tmdb_id, kind) if tmdb_id else None

            cur.execute("""
                UPDATE content
                SET thumbnail_url = %s,
                    backdrop_url  = %s,
                    youtube_trailer_id = %s
                WHERE id = %s
            """, (
                f"{IMG_BASE}{poster}",
                f"{BACKDROP_BASE}{backdrop}" if backdrop else None,
                trailer_id,
                row_id,
            ))
            updated += 1
            if updated % 20 == 0:
                conn.commit()
                print(f"  {updated} updated, {skipped} skipped so far…")
            time.sleep(0.05)  # ~20 req/s, well under TMDB's 40/s limit

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone — {updated} updated, {skipped} skipped (no TMDB match)")


if __name__ == "__main__":
    run()
