"""Seed ratings + rec_feedback so LTR retrain can actually fire.

Ratings are correlated with each user's DNA — high ratings go to titles
whose vibe matches the user's DNA closely. Feedback follows the same pattern.
"""
import os
import random
from sqlalchemy import create_engine, text

random.seed(42)
MOODS = ["happy", "tired", "focused", "alone", "with friends", "hungover", ""]
DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


def dna_match(user_row, content_row) -> float:
    dist = sum((float(user_row[f"dna_{d}"]) - float(content_row[f"vibe_{d}"])) ** 2 for d in DIMS) ** 0.5
    return max(0.0, 1.0 - dist / (len(DIMS) ** 0.5))


def main():
    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    eng = create_engine(url)
    with eng.begin() as c:
        users = c.execute(text(
            "SELECT id, dna_pace, dna_emotion, dna_darkness, dna_humor, dna_complexity, dna_spectacle FROM users LIMIT 50"
        )).mappings().all()
        contents = c.execute(text("""
            SELECT id, vibe_pace, vibe_emotion, vibe_darkness, vibe_humor, vibe_complexity, vibe_spectacle
            FROM content WHERE is_active = true ORDER BY popularity_score DESC LIMIT 150
        """)).mappings().all()

        ratings_inserted = 0
        for u in users:
            sample = random.sample(contents, k=6)
            for cr in sample:
                match = dna_match(u, cr)
                if match > 0.8:
                    rating = random.choice([4, 5, 5])
                elif match > 0.6:
                    rating = random.choice([3, 4])
                elif match > 0.4:
                    rating = random.choice([2, 3])
                else:
                    rating = random.choice([1, 2])
                try:
                    c.execute(text("""
                        INSERT INTO ratings (user_id, content_id, rating, mood_tag, rated_at)
                        VALUES (:u, :cid, :r, :m, now() - (random() * interval '30 days'))
                        ON CONFLICT DO NOTHING
                    """), {"u": str(u["id"]), "cid": str(cr["id"]), "r": rating,
                           "m": random.choice(MOODS) or None})
                    ratings_inserted += 1
                except Exception:
                    continue

        feedback_inserted = 0
        for u in users[:30]:
            for _ in range(3):
                cr = random.choice(contents)
                match = dna_match(u, cr)
                fb = 1 if match > 0.7 else (-1 if match < 0.4 else 0)
                if fb == 0: continue
                try:
                    c.execute(text("""
                        INSERT INTO rec_feedback (user_id, content_id, surface, feedback)
                        VALUES (:u, :c, 'home', :f)
                    """), {"u": str(u["id"]), "c": str(cr["id"]), "f": fb})
                    feedback_inserted += 1
                except Exception:
                    continue

        # Also populate chat_feedback so LLM-usage data is real
        for u in users[:10]:
            c.execute(text("""
                INSERT INTO chat_feedback (user_id, turn_index, user_message, assistant_message, feedback)
                VALUES (:u, 1, 'recommend me a thriller', 'Try Memento — it fits your complexity DNA.', 1),
                       (:u, 3, 'something funny', 'The Grand Budapest Hotel is a good bet.', 1)
            """), {"u": str(u["id"])})

    print(f"ratings={ratings_inserted} rec_feedback={feedback_inserted}")


if __name__ == "__main__":
    main()
