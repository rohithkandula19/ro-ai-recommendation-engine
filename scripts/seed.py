"""Seed the recommendation engine with realistic fake data.

Two phases:
  DB phase: genres, content, users, interactions, popularity
  ML phase (conditional on imports): embeddings → FAISS, ALS model, snapshots

The DB phase needs only SQLAlchemy + psycopg2 + passlib + Faker and can run
inside the `api` docker container. The ML phase should run inside the
`ml_service` container or a venv with ML deps.

Usage:
    python scripts/seed.py              # both phases if ML deps available
    python scripts/seed.py --db-only    # skip ML phase
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from faker import Faker
from loguru import logger
from passlib.hash import bcrypt
from sqlalchemy import create_engine, text
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
fake = Faker()
random.seed(42)
np.random.seed(42)

DB_URL = os.getenv(
    "SYNC_DATABASE_URL",
    "postgresql://recuser:recpass@localhost:5432/recengine",
)

GENRES = [
    "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "Film-Noir", "History", "Horror", "Music", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Sport", "Thriller", "War", "Western",
    "Superhero", "Anime", "Reality-TV", "Talk-Show", "Game-Show", "News", "Short",
    "Dark Comedy", "Political", "Legal", "Medical", "Space Opera", "Cyberpunk",
    "Post-Apocalyptic", "Spy", "Heist", "Noir", "Parody", "Satire", "Slice of Life",
    "Martial Arts", "Musical Drama", "Psychological", "Teen", "Period Drama",
    "Historical Fiction", "Mockumentary", "Disaster",
][:50]

TITLE_PARTS = [
    ["The", "A", "Last", "First", "Silent", "Dark", "Bright", "Lost", "Hidden", "Final"],
    ["Echo", "Shadow", "Light", "Storm", "River", "Mountain", "Signal", "Harbor", "Fortress", "Garden", "Kingdom", "Empire", "Machine", "Algorithm", "Horizon"],
    ["of", "in", "from", "beyond", "under"],
    ["Midnight", "Tomorrow", "Yesterday", "Dawn", "Dusk", "Glass", "Iron", "Fire", "Water", "Fate"],
]
MATURITY = ["G", "PG", "PG-13", "R", "TV-14", "TV-MA"]
LANGUAGES = ["en", "es", "fr", "de", "ja", "ko"]

CONF_BY_EVENT = {
    "click": 0.3, "play": 1.0, "complete": 3.0, "like": 2.0,
    "add_to_list": 1.5, "rate": 2.0, "dislike": -1.0,
}

VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")

GENRE_VIBES = {
    "Action":       {"pace": 0.90, "emotion": 0.50, "darkness": 0.55, "humor": 0.40, "complexity": 0.30, "spectacle": 0.90},
    "Adventure":    {"pace": 0.75, "emotion": 0.55, "darkness": 0.35, "humor": 0.55, "complexity": 0.40, "spectacle": 0.85},
    "Animation":    {"pace": 0.60, "emotion": 0.65, "darkness": 0.25, "humor": 0.70, "complexity": 0.40, "spectacle": 0.75},
    "Biography":    {"pace": 0.35, "emotion": 0.75, "darkness": 0.50, "humor": 0.30, "complexity": 0.65, "spectacle": 0.35},
    "Comedy":       {"pace": 0.65, "emotion": 0.50, "darkness": 0.20, "humor": 0.95, "complexity": 0.30, "spectacle": 0.40},
    "Crime":        {"pace": 0.55, "emotion": 0.55, "darkness": 0.75, "humor": 0.25, "complexity": 0.70, "spectacle": 0.45},
    "Documentary":  {"pace": 0.30, "emotion": 0.55, "darkness": 0.45, "humor": 0.30, "complexity": 0.75, "spectacle": 0.25},
    "Drama":        {"pace": 0.40, "emotion": 0.85, "darkness": 0.55, "humor": 0.30, "complexity": 0.65, "spectacle": 0.35},
    "Family":       {"pace": 0.55, "emotion": 0.60, "darkness": 0.15, "humor": 0.70, "complexity": 0.30, "spectacle": 0.55},
    "Fantasy":      {"pace": 0.60, "emotion": 0.60, "darkness": 0.40, "humor": 0.50, "complexity": 0.55, "spectacle": 0.90},
    "Horror":       {"pace": 0.55, "emotion": 0.55, "darkness": 0.95, "humor": 0.20, "complexity": 0.45, "spectacle": 0.60},
    "Mystery":      {"pace": 0.45, "emotion": 0.60, "darkness": 0.70, "humor": 0.30, "complexity": 0.85, "spectacle": 0.40},
    "Romance":      {"pace": 0.35, "emotion": 0.90, "darkness": 0.30, "humor": 0.50, "complexity": 0.45, "spectacle": 0.35},
    "Sci-Fi":       {"pace": 0.65, "emotion": 0.50, "darkness": 0.55, "humor": 0.40, "complexity": 0.85, "spectacle": 0.90},
    "Thriller":     {"pace": 0.70, "emotion": 0.60, "darkness": 0.80, "humor": 0.25, "complexity": 0.70, "spectacle": 0.55},
    "War":          {"pace": 0.65, "emotion": 0.80, "darkness": 0.85, "humor": 0.20, "complexity": 0.60, "spectacle": 0.75},
    "Cyberpunk":    {"pace": 0.70, "emotion": 0.45, "darkness": 0.75, "humor": 0.35, "complexity": 0.85, "spectacle": 0.85},
    "Psychological":{"pace": 0.40, "emotion": 0.70, "darkness": 0.80, "humor": 0.20, "complexity": 0.95, "spectacle": 0.35},
    "Musical":      {"pace": 0.55, "emotion": 0.85, "darkness": 0.20, "humor": 0.70, "complexity": 0.40, "spectacle": 0.75},
    "Superhero":    {"pace": 0.85, "emotion": 0.55, "darkness": 0.50, "humor": 0.60, "complexity": 0.40, "spectacle": 0.95},
}

DEFAULT_VIBE = {"pace": 0.5, "emotion": 0.5, "darkness": 0.5, "humor": 0.5, "complexity": 0.5, "spectacle": 0.5}


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def vibe_for_genres(genres: list[str]) -> dict[str, float]:
    acc = {d: 0.0 for d in VIBE_DIMS}
    n = 0
    for g in genres:
        prior = GENRE_VIBES.get(g, DEFAULT_VIBE)
        for d in VIBE_DIMS:
            acc[d] += prior[d]
        n += 1
    if n == 0:
        return dict(DEFAULT_VIBE)
    return {d: _clip(acc[d] / n + random.gauss(0, 0.08)) for d in VIBE_DIMS}


def mood_from_vibe(v: dict[str, float]) -> tuple[float, float]:
    chill_tense = _clip(0.5 * v["darkness"] + 0.35 * v["pace"] + 0.15 * (1 - v["humor"]))
    light_thoughtful = _clip(0.55 * v["complexity"] + 0.25 * (1 - v["spectacle"]) + 0.2 * v["emotion"])
    return chill_tense, light_thoughtful


def estimate_completion_rate(duration_seconds: int, typ: str, v: dict[str, float]) -> float:
    minutes = (duration_seconds or 1800) / 60.0
    length_penalty = 1.0 if minutes < 45 else (0.9 if minutes < 90 else (0.75 if minutes < 150 else 0.65))
    if typ == "series":
        length_penalty += 0.08
    base = 0.55 + 0.18 * v["humor"] + 0.12 * v["spectacle"] - 0.18 * v["darkness"] - 0.12 * v["complexity"]
    return _clip(base * length_penalty + random.gauss(0, 0.04))


def make_title() -> str:
    return " ".join(random.choice(col) for col in TITLE_PARTS)


def reset(engine):
    with engine.begin() as c:
        c.execute(text(
            "TRUNCATE TABLE recommendation_snapshots, watchlist, ratings, "
            "watch_history, user_preferences, interactions, content, genres, users "
            "RESTART IDENTITY CASCADE"
        ))
    logger.info("Database reset")


def seed_genres(engine, extra: list[str] | None = None) -> dict[str, int]:
    all_genres = list(GENRES)
    for g in extra or []:
        if g and g not in all_genres:
            all_genres.append(g)
    with engine.begin() as c:
        for g in all_genres:
            c.execute(
                text("INSERT INTO genres (name, slug) VALUES (:n, :s) ON CONFLICT DO NOTHING"),
                {"n": g, "s": g.lower().replace(" ", "-")},
            )
        rows = c.execute(text("SELECT id, name FROM genres")).all()
    return {name: gid for gid, name in rows}


def _poster_url(entry: dict) -> str:
    poster = entry.get("poster", "")
    if not poster:
        return f"https://picsum.photos/seed/{entry.get('title','x')}/400/225"
    if poster.startswith("http"):
        return poster
    return f"https://image.tmdb.org/t/p/w500{poster}"


def _load_real_content() -> list[dict]:
    """Load real titles from curated movies + tvmaze TV ingestion."""
    out: list[dict] = []
    for fname in ("real_content.json", "trakt_ingested.json", "tvmaze_ingested.json", "tmdb_ingested.json", "omdb_enriched.json"):
        p = Path(__file__).parent / fname
        if p.exists():
            try:
                data = json.loads(p.read_text())
                out.extend(data.get("titles", []))
                logger.info(f"Loaded {len(data.get('titles', []))} titles from {fname}")
            except Exception as e:
                logger.warning(f"Failed to load {fname}: {e}")
    seen = set()
    dedup = []
    for t in out:
        key = (t.get("title"), t.get("year"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(t)
    return dedup


def seed_content(engine, genre_map: dict[str, int], n: int = 1000) -> list[dict]:
    real = _load_real_content()
    if not real:
        logger.warning("No real content found — falling back to synthetic")
        return _seed_content_synthetic(engine, genre_map, n)

    records = []
    with engine.begin() as c:
        for entry in tqdm(real, desc="content"):
            cid = uuid.uuid4()
            title = entry["title"]
            typ = entry.get("type", "movie")
            g_sample = [g for g in entry.get("genres", []) if g in genre_map]
            if not g_sample:
                g_sample = ["Drama"]
                if "Drama" not in genre_map:
                    continue
            g_ids = [genre_map[g] for g in g_sample]
            runtime_min = entry.get("runtime_min") or 90
            duration = int(runtime_min) * 60
            year = entry.get("year") or 2000
            desc = entry.get("description") or ""
            thumb = _poster_url(entry)
            trailer = entry.get("trailer_url") or "https://www.w3schools.com/html/mov_bbb.mp4"
            cast = entry.get("cast") or []
            director = entry.get("director") or ""
            maturity = entry.get("rating") or ("TV-14" if typ == "series" else "PG-13")
            lang = "en"
            vibe = vibe_for_genres(g_sample)
            ct, lt = mood_from_vibe(vibe)
            comp = estimate_completion_rate(duration, typ, vibe)
            c.execute(text("""
                INSERT INTO content (id, title, type, genre_ids, release_year, duration_seconds, language,
                                     maturity_rating, description, thumbnail_url, trailer_url, cast_names, director,
                                     popularity_score, is_active,
                                     vibe_pace, vibe_emotion, vibe_darkness, vibe_humor, vibe_complexity, vibe_spectacle,
                                     mood_chill_tense, mood_light_thoughtful, completion_rate)
                VALUES (:id, :title, :type, :genre_ids, :year, :duration, :lang, :maturity, :desc,
                        :thumb, :trailer, :cast, :director, 0, true,
                        :vp, :ve, :vd, :vh, :vc, :vs, :ct, :lt, :comp)
            """), {
                "id": str(cid), "title": title, "type": typ, "genre_ids": g_ids,
                "year": year, "duration": duration, "lang": lang, "maturity": maturity,
                "desc": desc, "thumb": thumb, "trailer": trailer,
                "cast": cast, "director": director,
                "vp": vibe["pace"], "ve": vibe["emotion"], "vd": vibe["darkness"],
                "vh": vibe["humor"], "vc": vibe["complexity"], "vs": vibe["spectacle"],
                "ct": ct, "lt": lt, "comp": comp,
            })
            records.append({
                "id": str(cid), "title": title, "type": typ, "genre_ids": g_ids,
                "genres_joined": "|".join(g_sample), "description": desc,
                "maturity_rating": maturity, "vibe": vibe, "mood": (ct, lt), "completion": comp,
            })
    logger.info(f"Seeded {len(records)} REAL content items")
    return records


def _seed_content_synthetic(engine, genre_map: dict[str, int], n: int = 1000) -> list[dict]:
    records = []
    with engine.begin() as c:
        for _ in tqdm(range(n), desc="content"):
            cid = uuid.uuid4()
            title = make_title()
            g_sample = random.sample(GENRES, k=random.randint(1, 3))
            g_ids = [genre_map[g] for g in g_sample]
            typ = random.choices(["movie", "series", "short"], weights=[0.6, 0.35, 0.05])[0]
            duration = random.randint(600, 8400) if typ != "short" else random.randint(180, 900)
            year = random.randint(1970, 2025)
            desc = fake.paragraph(nb_sentences=4)
            thumb = f"https://picsum.photos/seed/{cid.hex[:8]}/400/225"
            trailer = "https://www.w3schools.com/html/mov_bbb.mp4"
            cast = [fake.name() for _ in range(random.randint(2, 6))]
            director = fake.name()
            maturity = random.choice(MATURITY)
            lang = random.choice(LANGUAGES)
            vibe = vibe_for_genres(g_sample)
            ct, lt = mood_from_vibe(vibe)
            comp = estimate_completion_rate(duration, typ, vibe)
            c.execute(text("""
                INSERT INTO content (id, title, type, genre_ids, release_year, duration_seconds, language,
                                     maturity_rating, description, thumbnail_url, trailer_url, cast_names, director,
                                     popularity_score, is_active,
                                     vibe_pace, vibe_emotion, vibe_darkness, vibe_humor, vibe_complexity, vibe_spectacle,
                                     mood_chill_tense, mood_light_thoughtful, completion_rate)
                VALUES (:id, :title, :type, :genre_ids, :year, :duration, :lang, :maturity, :desc,
                        :thumb, :trailer, :cast, :director, 0, true,
                        :vp, :ve, :vd, :vh, :vc, :vs, :ct, :lt, :comp)
            """), {
                "id": str(cid), "title": title, "type": typ, "genre_ids": g_ids,
                "year": year, "duration": duration, "lang": lang, "maturity": maturity,
                "desc": desc, "thumb": thumb, "trailer": trailer,
                "cast": cast, "director": director,
                "vp": vibe["pace"], "ve": vibe["emotion"], "vd": vibe["darkness"],
                "vh": vibe["humor"], "vc": vibe["complexity"], "vs": vibe["spectacle"],
                "ct": ct, "lt": lt, "comp": comp,
            })
            records.append({
                "id": str(cid), "title": title, "type": typ, "genre_ids": g_ids,
                "genres_joined": "|".join(g_sample), "description": desc,
                "maturity_rating": maturity, "vibe": vibe, "mood": (ct, lt), "completion": comp,
            })
    logger.info(f"Seeded {len(records)} synthetic content items")
    return records


def seed_users(engine, n: int = 500) -> list[str]:
    ids = []
    hashed = bcrypt.hash("password123")
    with engine.begin() as c:
        for i in tqdm(range(n), desc="users"):
            uid = uuid.uuid4()
            email = f"user{i}@example.com"
            name = fake.name()
            c.execute(text("""
                INSERT INTO users (id, email, hashed_password, display_name, is_active, is_admin)
                VALUES (:id, :email, :hp, :dn, true, :admin)
                ON CONFLICT (email) DO NOTHING
            """), {"id": str(uid), "email": email, "hp": hashed, "dn": name, "admin": i == 0})
            c.execute(
                text("INSERT INTO user_preferences (user_id, genre_ids) VALUES (:uid, :g) ON CONFLICT DO NOTHING"),
                {"uid": str(uid), "g": random.sample(range(1, 51), k=random.randint(2, 6))},
            )
            ids.append(str(uid))
    logger.info(f"Seeded {len(ids)} users. Password: 'password123'. Admin: user0@example.com")
    return ids


def seed_interactions(engine, user_ids: list[str], content_ids: list[str], n: int = 50000) -> list[dict]:
    pop = np.random.zipf(1.8, size=len(content_ids)).astype(float)
    c_probs = pop / pop.sum()
    now = datetime.now(timezone.utc)
    events = ["click", "play", "complete", "like", "add_to_list", "rate", "dislike"]
    ev_weights = [0.35, 0.30, 0.15, 0.08, 0.05, 0.04, 0.03]

    rows = []
    with engine.begin() as c:
        for _ in tqdm(range(n), desc="interactions"):
            uid = random.choice(user_ids)
            cid = str(np.random.choice(content_ids, p=c_probs))
            etype = random.choices(events, weights=ev_weights)[0]
            val = random.randint(1, 5) if etype == "rate" else None
            ts = now - timedelta(minutes=random.randint(0, 60 * 24 * 30))
            sid = uuid.uuid4()
            device = random.choice(["desktop", "mobile", "tablet", "tv"])
            c.execute(text("""
                INSERT INTO interactions (user_id, content_id, event_type, value, session_id, device_type, created_at)
                VALUES (:u, :c, :e, :v, :s, :d, :t)
            """), {"u": uid, "c": cid, "e": etype, "v": val, "s": str(sid), "d": device, "t": ts})

            if etype in ("play", "complete"):
                c.execute(text("""
                    INSERT INTO watch_history (user_id, content_id, watch_pct, total_seconds_watched, completed, last_watched_at, watch_count)
                    VALUES (:u, :c, :pct, :tsec, :done, :ts, 1)
                    ON CONFLICT (user_id, content_id) DO UPDATE
                    SET watch_pct = GREATEST(watch_history.watch_pct, EXCLUDED.watch_pct),
                        total_seconds_watched = watch_history.total_seconds_watched + EXCLUDED.total_seconds_watched,
                        completed = watch_history.completed OR EXCLUDED.completed,
                        last_watched_at = EXCLUDED.last_watched_at,
                        watch_count = watch_history.watch_count + 1
                """), {
                    "u": uid, "c": cid,
                    "pct": 1.0 if etype == "complete" else random.uniform(0.05, 0.95),
                    "tsec": random.randint(120, 5400),
                    "done": etype == "complete", "ts": ts,
                })
            rows.append({"user_id": uid, "content_id": cid, "event_type": etype, "value": val, "timestamp": ts})

    logger.info("Recomputing content popularity_score")
    with engine.begin() as c:
        c.execute(text("""
            UPDATE content SET popularity_score = p.score FROM (
                SELECT content_id, COUNT(*)::float / 1000.0 AS score
                FROM interactions WHERE event_type IN ('click','play','complete','like','add_to_list')
                GROUP BY content_id
            ) p WHERE content.id = p.content_id
        """))
    return rows


def compute_user_dna(engine) -> None:
    """Aggregate each user's taste DNA from the vibe vectors of content they've engaged with, weighted by event strength."""
    logger.info("Computing user taste_dna from watch history")
    with engine.begin() as c:
        c.execute(text(f"""
            WITH weighted AS (
                SELECT i.user_id,
                       SUM(CASE i.event_type
                               WHEN 'complete' THEN 3.0
                               WHEN 'like' THEN 2.0
                               WHEN 'rate' THEN COALESCE(i.value, 3) - 2.0
                               WHEN 'add_to_list' THEN 1.5
                               WHEN 'play' THEN 1.0
                               WHEN 'click' THEN 0.3
                               WHEN 'dislike' THEN -1.5
                               ELSE 0 END) AS total_w,
                       {", ".join([
                           f"SUM(CASE i.event_type WHEN 'complete' THEN 3.0 WHEN 'like' THEN 2.0 WHEN 'add_to_list' THEN 1.5 WHEN 'play' THEN 1.0 WHEN 'click' THEN 0.3 WHEN 'dislike' THEN -1.5 ELSE 0 END * c.vibe_{d}) AS sum_{d}"
                           for d in VIBE_DIMS
                       ])},
                       COUNT(*) AS samples
                FROM interactions i JOIN content c ON c.id = i.content_id
                GROUP BY i.user_id
            )
            UPDATE users u SET
                {", ".join([f"dna_{d} = CASE WHEN w.total_w > 0 THEN LEAST(1, GREATEST(0, w.sum_{d} / w.total_w)) ELSE 0.5 END" for d in VIBE_DIMS])},
                dna_samples = w.samples
            FROM weighted w
            WHERE u.id = w.user_id
        """))


def ml_phase(content_records, interactions, user_ids, artifacts_dir: Path, engine):
    try:
        for candidate in [ROOT / "backend" / "ml_service", Path("/app")]:
            if (candidate / "core" / "faiss_index.py").exists():
                sys.path.insert(0, str(candidate))
                break
        from core.faiss_index import FaissIndex  # type: ignore
        from models.embeddings import TextEmbedder  # type: ignore
        from models.als_model import ALSRecommender  # type: ignore
    except Exception as e:
        logger.warning(f"ML phase skipped (deps missing): {e}")
        return

    import pandas as pd
    logger.info("Embedding content...")
    embedder = TextEmbedder("all-MiniLM-L6-v2")
    texts = [
        embedder.build_text(r["title"], r["description"], r.get("genres_joined", "").split("|"))
        for r in content_records
    ]
    emb = embedder.encode(texts, batch_size=64)
    idx = FaissIndex(dim=emb.shape[1], nlist=100, m=8)
    idx.build(emb, [r["id"] for r in content_records])
    (artifacts_dir / "faiss").mkdir(parents=True, exist_ok=True)
    idx.save(str(artifacts_dir / "faiss"))
    logger.info(f"Saved FAISS index to {artifacts_dir / 'faiss'}")

    df = pd.DataFrame(interactions)
    df = df[df["event_type"].isin(CONF_BY_EVENT.keys())].copy()
    df["confidence"] = df["event_type"].map(CONF_BY_EVENT)
    agg = df.groupby(["user_id", "content_id"], as_index=False)["confidence"].sum()
    agg = agg[agg["confidence"] > 0]
    rows = [(str(r.user_id), str(r.content_id), float(r.confidence)) for r in agg.itertuples(index=False)]
    als = ALSRecommender(factors=64, iterations=15, regularization=0.01)
    als.fit(rows)
    (artifacts_dir / "als").mkdir(parents=True, exist_ok=True)
    als.save(str(artifacts_dir / "als"))
    logger.info("Saved ALS model")

    now = datetime.now(timezone.utc)
    with engine.begin() as c:
        for uid in tqdm(user_ids[:100], desc="snapshots"):
            recs = als.recommend(uid, n=40)
            if not recs:
                continue
            c.execute(text("""
                INSERT INTO recommendation_snapshots (user_id, surface, content_ids, scores, model_version, generated_at, expires_at)
                VALUES (:uid, 'home', CAST(:cids AS uuid[]), :scores, 'v1', :now, :exp)
                ON CONFLICT (user_id, surface) DO UPDATE
                  SET content_ids = EXCLUDED.content_ids, scores = EXCLUDED.scores,
                      model_version = EXCLUDED.model_version, generated_at = EXCLUDED.generated_at,
                      expires_at = EXCLUDED.expires_at
            """), {"uid": uid, "cids": [r[0] for r in recs], "scores": [float(r[1]) for r in recs],
                   "now": now, "exp": now + timedelta(hours=6)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--users", type=int, default=500)
    parser.add_argument("--content", type=int, default=1000)
    parser.add_argument("--interactions", type=int, default=50000)
    parser.add_argument("--db-url", default=DB_URL)
    parser.add_argument("--artifacts-dir", default=str(ROOT / "backend" / "ml_service" / "artifacts"))
    parser.add_argument("--db-only", action="store_true")
    args = parser.parse_args()

    engine = create_engine(args.db_url)
    artifacts = Path(args.artifacts_dir)

    if args.reset:
        reset(engine)
    # Precompute all genres we'll need (from real content) before creating content
    real_for_genres = _load_real_content()
    extra_genres = sorted({g for t in real_for_genres for g in (t.get("genres") or [])})
    genre_map = seed_genres(engine, extra=extra_genres)
    content_records = seed_content(engine, genre_map, n=args.content)
    user_ids = seed_users(engine, n=args.users)
    interactions = seed_interactions(engine, user_ids, [r["id"] for r in content_records], n=args.interactions)
    compute_user_dna(engine)
    if not args.db_only:
        ml_phase(content_records, interactions, user_ids, artifacts, engine)

    logger.success("Seeding complete.")


if __name__ == "__main__":
    main()
