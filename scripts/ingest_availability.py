"""Populate content_availability from TMDB /watch/providers (JustWatch data).

Matches existing content rows by (title, release_year), queries TMDB for each,
then inserts one row per provider per offer-type. Region defaults to US — pass
REGIONS=US,GB,CA to populate multiple.

    TMDB_API_KEY=xxx SYNC_DATABASE_URL=... python scripts/ingest_availability.py
"""
from __future__ import annotations

import os
import time
from urllib.parse import quote

import httpx
from sqlalchemy import create_engine, text

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_KEY = os.getenv("TMDB_API_KEY")
REGIONS = [r.strip().upper() for r in os.getenv("REGIONS", "US").split(",") if r.strip()]

PROVIDER_DEEP_LINKS = {
    "Netflix": "https://www.netflix.com/search?q={q}",
    "Amazon Prime Video": "https://www.amazon.com/s?k={q}&i=instant-video",
    "Disney Plus": "https://www.disneyplus.com/search?q={q}",
    "Hulu": "https://www.hulu.com/search?q={q}",
    "Max": "https://play.max.com/search?q={q}",
    "HBO Max": "https://play.max.com/search?q={q}",
    "Apple TV Plus": "https://tv.apple.com/search?term={q}",
    "Apple TV": "https://tv.apple.com/search?term={q}",
    "Peacock": "https://www.peacocktv.com/search?q={q}",
    "Paramount Plus": "https://www.paramountplus.com/search/?query={q}",
    "YouTube": "https://www.youtube.com/results?search_query={q}",
    "Google Play Movies": "https://play.google.com/store/search?q={q}&c=movies",
    "Vudu": "https://www.vudu.com/content/movies/search?searchString={q}",
    "Tubi TV": "https://tubitv.com/search/{q}",
    "Pluto TV": "https://pluto.tv/en/search/details?query={q}",
    "Freevee": "https://www.amazon.com/gp/video/storefront/?contentType=merchandised_hub",
    "Crunchyroll": "https://www.crunchyroll.com/search?from=&q={q}",
    "Starz": "https://www.starz.com/us/en/search/{q}",
    "Showtime": "https://www.sho.com/search/{q}",
    "AMC Plus": "https://www.amcplus.com/search?q={q}",
}

OFFER_MAP = {"flatrate": "stream", "free": "free", "ads": "free", "rent": "rent", "buy": "buy"}


def main() -> None:
    if not TMDB_KEY:
        raise SystemExit("TMDB_API_KEY required")

    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    eng = create_engine(url)
    inserted = 0
    skipped = 0

    with eng.begin() as c:
        rows = c.execute(text("""
            SELECT id, title, type, release_year FROM content
            WHERE is_active = true AND release_year IS NOT NULL
            ORDER BY popularity_score DESC LIMIT 400
        """)).mappings().all()

    with httpx.Client(timeout=15) as client:
        for row in rows:
            tmdb_type = "movie" if row["type"] == "movie" else "tv"
            q = quote(row["title"])
            try:
                s = client.get(
                    f"{TMDB_BASE}/search/{tmdb_type}",
                    params={"api_key": TMDB_KEY, "query": row["title"], "year": row["release_year"]},
                ).json()
                results = s.get("results", [])
                if not results:
                    skipped += 1
                    continue
                tmdb_id = results[0]["id"]

                pv = client.get(
                    f"{TMDB_BASE}/{tmdb_type}/{tmdb_id}/watch/providers",
                    params={"api_key": TMDB_KEY},
                ).json().get("results", {})
            except Exception:
                skipped += 1
                continue

            for region in REGIONS:
                region_data = pv.get(region)
                if not region_data:
                    continue
                for raw_offer_type, offer_type in OFFER_MAP.items():
                    for provider in region_data.get(raw_offer_type, []) or []:
                        name = provider.get("provider_name", "")
                        logo = provider.get("logo_path")
                        template = PROVIDER_DEEP_LINKS.get(name)
                        if template:
                            link = template.format(q=q)
                        else:
                            link = region_data.get("link") or f"https://www.themoviedb.org/{tmdb_type}/{tmdb_id}/watch"
                        logo_url = f"https://image.tmdb.org/t/p/w92{logo}" if logo else None
                        try:
                            with eng.begin() as c:
                                c.execute(text("""
                                    INSERT INTO content_availability
                                      (content_id, provider, provider_logo, offer_type, deep_link, region)
                                    VALUES (:cid, :p, :l, :o, :d, :r)
                                    ON CONFLICT ON CONSTRAINT uq_availability DO UPDATE
                                      SET provider_logo = EXCLUDED.provider_logo,
                                          deep_link = EXCLUDED.deep_link,
                                          updated_at = now()
                                """), {
                                    "cid": str(row["id"]), "p": name, "l": logo_url,
                                    "o": offer_type, "d": link, "r": region,
                                })
                            inserted += 1
                        except Exception:
                            continue
            time.sleep(0.25)

    print(f"inserted={inserted} skipped={skipped}")


if __name__ == "__main__":
    main()
