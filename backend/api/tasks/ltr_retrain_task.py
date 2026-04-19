"""Nightly LightGBM LTR retrain using rec_feedback + content/user signals.

Pulls every feedback event, joins user DNA + content vibe + popularity, produces
a feature matrix labelled by feedback (+1/-1/0 mapped to 2/0/1), trains a ranker,
writes to the shared /app/artifacts/ranker/ltr.txt volume that ml_service reads.
"""
import os
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text

from tasks.celery_app import celery_app


VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")
FEATURE_NAMES = [
    "user_age_days", "watch_count", "avg_watch_pct", "content_popularity",
    "genre_match_score", "release_recency", "cf_score", "cb_score",
    "trending_score", "session_score",
]


def _connect():
    url = os.getenv("SYNC_DATABASE_URL", "postgresql://recuser:recpass@postgres:5432/recengine")
    return create_engine(url)


def _build_features():
    import numpy as np
    eng = _connect()
    with eng.connect() as c:
        rows = c.execute(text("""
            SELECT f.user_id, f.content_id, f.feedback,
                   u.dna_pace, u.dna_emotion, u.dna_darkness, u.dna_humor, u.dna_complexity, u.dna_spectacle, u.dna_samples,
                   ct.popularity_score, ct.release_year, ct.completion_rate,
                   ct.vibe_pace, ct.vibe_emotion, ct.vibe_darkness, ct.vibe_humor, ct.vibe_complexity, ct.vibe_spectacle
            FROM rec_feedback f
            JOIN users u ON u.id = f.user_id
            JOIN content ct ON ct.id = f.content_id
        """)).mappings().all()
    groups: dict[str, list[int]] = {}
    X: list[list[float]] = []
    y: list[float] = []
    order: list[str] = []
    for r in rows:
        uid = str(r["user_id"])
        dna = np.array([r[f"dna_{d}"] for d in VIBE_DIMS], dtype=np.float32)
        vibe = np.array([r[f"vibe_{d}"] for d in VIBE_DIMS], dtype=np.float32)
        dist = float(np.linalg.norm(dna - vibe))
        dna_match = max(0.0, 1.0 - dist / (len(VIBE_DIMS) ** 0.5))
        feats = [
            float(r["dna_samples"]) / 100.0,
            0.0, 0.0,
            float(r["popularity_score"] or 0.0),
            dna_match,
            max(0.0, 1.0 - (2026 - int(r["release_year"] or 2000)) / 50.0),
            dna_match, dna_match, 0.0, 0.0,
        ]
        X.append(feats)
        label = {1: 2.0, 0: 1.0, -1: 0.0}.get(int(r["feedback"]), 1.0)
        y.append(label)
        groups.setdefault(uid, []).append(1)
        order.append(uid)
    if not X:
        return None, None, None
    # sort by user so groups are contiguous
    sort_idx = sorted(range(len(order)), key=lambda i: order[i])
    X = np.array([X[i] for i in sort_idx], dtype=np.float32)
    y = np.array([y[i] for i in sort_idx], dtype=np.float32)
    order_sorted = [order[i] for i in sort_idx]
    # recompute group sizes
    group_sizes: list[int] = []
    last = None
    for uid in order_sorted:
        if uid != last:
            group_sizes.append(0)
            last = uid
        group_sizes[-1] += 1
    return X, y, group_sizes


def _train(X, y, groups, out_path: str):
    import lightgbm as lgb
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    train = lgb.Dataset(X, label=y, group=groups, feature_name=FEATURE_NAMES)
    params = {
        "objective": "lambdarank", "metric": "ndcg",
        "ndcg_eval_at": [5, 10, 20], "learning_rate": 0.05,
        "num_leaves": 31, "min_data_in_leaf": 2, "verbose": -1,
    }
    model = lgb.train(params, train, num_boost_round=200)
    model.save_model(out_path)


@celery_app.task(name="tasks.ltr_retrain_task.retrain_ltr_from_feedback")
def retrain_ltr_from_feedback() -> dict:
    logger.info("LTR retrain: loading feedback")
    X, y, groups = _build_features()
    if X is None or len(X) < 10:
        return {"status": "skipped", "reason": "not enough feedback", "samples": 0 if X is None else len(X)}
    out = "/app/artifacts/ranker/ltr.txt"
    # Note: this path only exists inside ml_service container. The celery worker
    # uses the same backend/api image which has artifacts/ mounted from ml_service
    # when docker-compose shares volumes. For local dev we write here and the
    # ml_service reload pulls on restart.
    _train(X, y, groups, out)
    logger.info(f"LTR retrained on {len(X)} feedback rows → {out}")
    return {"status": "ok", "samples": int(len(X)), "groups": len(groups), "artifact": out}
