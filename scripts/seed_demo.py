"""Seed demo content: personas, real reviews, streaming availability, feature flags.

Runs idempotently inside docker: docker exec infra-api-1 python /tmp/seed_demo.py
"""
import os
import random
import uuid
from sqlalchemy import create_engine, text

URL = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
eng = create_engine(URL)

PERSONAS = [
    {"email": "persona-thriller@example.com", "name": "Thriller Fan",
     "genres": ["Thriller", "Crime", "Mystery"],
     "dna": {"pace": 0.8, "emotion": 0.55, "darkness": 0.8, "humor": 0.25, "complexity": 0.75, "spectacle": 0.6}},
    {"email": "persona-anime@example.com", "name": "Anime Watcher",
     "genres": ["Animation", "Fantasy", "Action"],
     "dna": {"pace": 0.7, "emotion": 0.7, "darkness": 0.5, "humor": 0.55, "complexity": 0.6, "spectacle": 0.9}},
    {"email": "persona-comfort@example.com", "name": "Comfort Watcher",
     "genres": ["Comedy", "Romance", "Family"],
     "dna": {"pace": 0.4, "emotion": 0.65, "darkness": 0.2, "humor": 0.85, "complexity": 0.35, "spectacle": 0.4}},
    {"email": "persona-auteur@example.com", "name": "Arthouse Fan",
     "genres": ["Drama", "Biography", "Foreign"],
     "dna": {"pace": 0.3, "emotion": 0.85, "darkness": 0.7, "humor": 0.3, "complexity": 0.95, "spectacle": 0.3}},
    {"email": "persona-scifi@example.com", "name": "Sci-Fi Head",
     "genres": ["Sci-Fi", "Thriller"],
     "dna": {"pace": 0.65, "emotion": 0.5, "darkness": 0.6, "humor": 0.4, "complexity": 0.85, "spectacle": 0.9}},
    {"email": "persona-horror@example.com", "name": "Horror Obsessive",
     "genres": ["Horror", "Thriller"],
     "dna": {"pace": 0.55, "emotion": 0.55, "darkness": 0.95, "humor": 0.2, "complexity": 0.5, "spectacle": 0.55}},
    {"email": "persona-doc@example.com", "name": "Documentary Nerd",
     "genres": ["Documentary", "Biography", "History"],
     "dna": {"pace": 0.3, "emotion": 0.55, "darkness": 0.45, "humor": 0.35, "complexity": 0.8, "spectacle": 0.25}},
    {"email": "persona-action@example.com", "name": "Action Junkie",
     "genres": ["Action", "Adventure"],
     "dna": {"pace": 0.95, "emotion": 0.5, "darkness": 0.55, "humor": 0.45, "complexity": 0.3, "spectacle": 0.95}},
    {"email": "persona-kids@example.com", "name": "Family Viewer",
     "genres": ["Family", "Animation", "Adventure"],
     "dna": {"pace": 0.55, "emotion": 0.65, "darkness": 0.15, "humor": 0.7, "complexity": 0.3, "spectacle": 0.7}},
    {"email": "persona-sports@example.com", "name": "Sports Watcher",
     "genres": ["Sport", "Biography"],
     "dna": {"pace": 0.75, "emotion": 0.7, "darkness": 0.35, "humor": 0.5, "complexity": 0.4, "spectacle": 0.75}},
]

REVIEW_TEMPLATES = [
    "Hit harder than I expected. The pacing never drags.",
    "Solid craft, but the ending felt rushed.",
    "I'd rewatch this on a rainy Sunday.",
    "Not for everyone, but it found me at the right time.",
    "Visually stunning; narratively thin.",
    "The lead performance carries the whole thing.",
    "Underrated — word of mouth should be louder.",
    "Clever premise, uneven execution.",
    "This ages like wine. Better every year.",
    "Genre-defining. No notes.",
]

STREAMING_SERVICES = ["Netflix", "Prime Video", "HBO Max", "Hulu", "Disney+", "Apple TV+"]
REGIONS = ["US", "GB", "CA", "AU", "IN"]


def main():
    from passlib.hash import bcrypt
    pw = bcrypt.hash("password123")
    with eng.begin() as c:
        # Personas
        for p in PERSONAS:
            uid = uuid.uuid4()
            c.execute(text("""
                INSERT INTO users (id, email, hashed_password, display_name, is_active,
                    dna_pace, dna_emotion, dna_darkness, dna_humor, dna_complexity, dna_spectacle, dna_samples)
                VALUES (:i, :e, :hp, :n, true, :dp, :de, :dd, :dh, :dc, :ds, 50)
                ON CONFLICT (email) DO UPDATE SET
                    dna_pace=:dp, dna_emotion=:de, dna_darkness=:dd,
                    dna_humor=:dh, dna_complexity=:dc, dna_spectacle=:ds
            """), {"i": str(uid), "e": p["email"], "hp": pw, "n": p["name"],
                   "dp": p["dna"]["pace"], "de": p["dna"]["emotion"], "dd": p["dna"]["darkness"],
                   "dh": p["dna"]["humor"], "dc": p["dna"]["complexity"], "ds": p["dna"]["spectacle"]})
            c.execute(text("INSERT INTO user_preferences (user_id) VALUES (:u) ON CONFLICT DO NOTHING"),
                      {"u": str(uid)})
            # Persona watch history: 30 titles matching their genre preferences
            titles = c.execute(text("""
                SELECT id FROM content WHERE is_active = true
                  AND EXISTS (
                    SELECT 1 FROM genres g WHERE g.id = ANY(content.genre_ids) AND g.name = ANY(:gs)
                  )
                ORDER BY popularity_score DESC LIMIT 30
            """), {"gs": p["genres"]}).scalars().all()
            for cid in titles[:25]:
                c.execute(text("""
                    INSERT INTO watch_history (user_id, content_id, watch_pct, completed, last_watched_at, watch_count)
                    VALUES (:u, :c, 1.0, true, now() - (random() * interval '30 days'), 1)
                    ON CONFLICT DO NOTHING
                """), {"u": str(uid), "c": str(cid)})

        # Reviews — 50 seeded
        users = [r[0] for r in c.execute(text("SELECT id FROM users LIMIT 20")).all()]
        contents = [r[0] for r in c.execute(text("SELECT id FROM content WHERE popularity_score > 0.005 LIMIT 30")).all()]
        for _ in range(50):
            if not users or not contents: break
            c.execute(text("""
                INSERT INTO reviews (user_id, content_id, body, has_spoilers, upvotes)
                VALUES (:u, :c, :b, :s, :v)
                ON CONFLICT DO NOTHING
            """), {"u": str(random.choice(users)), "c": str(random.choice(contents)),
                   "b": random.choice(REVIEW_TEMPLATES), "s": random.random() < 0.15,
                   "v": random.randint(0, 80)})

        # Streaming availability — random 3 services per top 100 titles
        top100 = [r[0] for r in c.execute(text(
            "SELECT id FROM content ORDER BY popularity_score DESC LIMIT 100"
        )).all()]
        for cid in top100:
            for svc in random.sample(STREAMING_SERVICES, k=random.randint(1, 3)):
                c.execute(text("""
                    INSERT INTO streaming_availability (content_id, service, region, deep_link)
                    VALUES (:c, :s, 'US', :d) ON CONFLICT DO NOTHING
                """), {"c": str(cid), "s": svc.lower().replace(" ", "-"),
                       "d": f"https://{svc.lower().replace(' ','')}.com/watch"})

        # Content regions — allow top 100 globally
        for cid in top100:
            c.execute(text("""
                INSERT INTO content_regions (content_id, allowed_regions)
                VALUES (:c, :r) ON CONFLICT DO NOTHING
            """), {"c": str(cid), "r": REGIONS})

        # Feature flags seed
        for k, pct in [("chat_v2", 100), ("rich_detail", 100), ("watch_party", 100),
                       ("ro_wrapped", 50), ("blind_date", 50), ("mixer", 50)]:
            c.execute(text("""
                INSERT INTO feature_flags (key, enabled, rollout_pct) VALUES (:k, true, :p)
                ON CONFLICT (key) DO UPDATE SET rollout_pct=:p
            """), {"k": k, "p": pct})

        # Backdrop URLs — copy thumbnail_url as fallback backdrop
        c.execute(text("""
            UPDATE content SET backdrop_url = thumbnail_url
            WHERE backdrop_url IS NULL AND thumbnail_url IS NOT NULL
        """))

        # Rec quality seed — add some fake impressions for the dashboard
        c.execute(text("""
            INSERT INTO rec_quality_daily (day, surface, impressions, clicks, plays, completes, likes, dislikes)
            VALUES
              (current_date, 'home', 1200, 340, 180, 85, 62, 8),
              (current_date, 'trending', 800, 220, 110, 45, 38, 5),
              (current_date - 1, 'home', 1100, 310, 165, 72, 54, 9),
              (current_date - 1, 'trending', 750, 198, 95, 40, 32, 6)
            ON CONFLICT DO NOTHING
        """))

    print("Demo seed: 10 personas, 50 reviews, 100 streaming rows, 6 flags, rec-quality seeded.")


if __name__ == "__main__":
    main()
