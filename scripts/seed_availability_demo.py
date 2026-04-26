"""Seed plausible provider availability for demo when no TMDB key is present.

Each top-N title gets 1-3 stream providers + rent/buy options with
search-query deep-links to the real services. Replace with
ingest_availability.py once a TMDB key is configured.
"""
import os
import random
from urllib.parse import quote

from sqlalchemy import create_engine, text

random.seed(7)

STREAM = [
    ("Netflix", "https://www.netflix.com/search?q={q}"),
    ("Amazon Prime Video", "https://www.amazon.com/s?k={q}&i=instant-video"),
    ("Max", "https://play.max.com/search?q={q}"),
    ("Disney Plus", "https://www.disneyplus.com/search?q={q}"),
    ("Hulu", "https://www.hulu.com/search?q={q}"),
    ("Apple TV Plus", "https://tv.apple.com/search?term={q}"),
    ("Peacock", "https://www.peacocktv.com/search?q={q}"),
]
RENT = [
    ("Apple TV", "https://tv.apple.com/search?term={q}", 3.99),
    ("Amazon Video", "https://www.amazon.com/s?k={q}&i=instant-video", 3.99),
    ("Google Play Movies", "https://play.google.com/store/search?q={q}&c=movies", 3.99),
]
BUY = [
    ("Apple TV", "https://tv.apple.com/search?term={q}", 14.99),
    ("Amazon Video", "https://www.amazon.com/s?k={q}&i=instant-video", 12.99),
    ("Vudu", "https://www.vudu.com/content/movies/search?searchString={q}", 9.99),
]
FREE = [
    ("Tubi TV", "https://tubitv.com/search/{q}"),
    ("Pluto TV", "https://pluto.tv/en/search/details?query={q}"),
    ("Freevee", "https://www.amazon.com/gp/video/storefront/?contentType=merchandised_hub"),
]


def main():
    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    eng = create_engine(url)
    inserted = 0
    with eng.begin() as c:
        rows = c.execute(text("""
            SELECT id, title FROM content WHERE is_active = true
            ORDER BY popularity_score DESC NULLS LAST LIMIT 300
        """)).mappings().all()

        for r in rows:
            q = quote(r["title"])
            streams = random.sample(STREAM, k=random.randint(1, 3))
            for name, tpl in streams:
                c.execute(text("""
                    INSERT INTO content_availability
                      (content_id, provider, offer_type, deep_link, region)
                    VALUES (:cid, :p, 'stream', :d, 'US')
                    ON CONFLICT ON CONSTRAINT uq_availability DO NOTHING
                """), {"cid": str(r["id"]), "p": name, "d": tpl.format(q=q)})
                inserted += 1
            if random.random() < 0.7:
                name, tpl, price = random.choice(RENT)
                c.execute(text("""
                    INSERT INTO content_availability
                      (content_id, provider, offer_type, deep_link, price, currency, region)
                    VALUES (:cid, :p, 'rent', :d, :pr, 'USD', 'US')
                    ON CONFLICT ON CONSTRAINT uq_availability DO NOTHING
                """), {"cid": str(r["id"]), "p": name, "d": tpl.format(q=q), "pr": price})
                inserted += 1
            if random.random() < 0.5:
                name, tpl, price = random.choice(BUY)
                c.execute(text("""
                    INSERT INTO content_availability
                      (content_id, provider, offer_type, deep_link, price, currency, region)
                    VALUES (:cid, :p, 'buy', :d, :pr, 'USD', 'US')
                    ON CONFLICT ON CONSTRAINT uq_availability DO NOTHING
                """), {"cid": str(r["id"]), "p": name, "d": tpl.format(q=q), "pr": price})
                inserted += 1
            if random.random() < 0.25:
                name, tpl = random.choice(FREE)
                c.execute(text("""
                    INSERT INTO content_availability
                      (content_id, provider, offer_type, deep_link, region)
                    VALUES (:cid, :p, 'free', :d, 'US')
                    ON CONFLICT ON CONSTRAINT uq_availability DO NOTHING
                """), {"cid": str(r["id"]), "p": name, "d": tpl.format(q=q)})
                inserted += 1

    print(f"availability_rows_inserted={inserted}")


if __name__ == "__main__":
    main()
