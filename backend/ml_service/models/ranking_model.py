import os
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np


FEATURE_NAMES = [
    "user_age_days", "watch_count", "avg_watch_pct", "content_popularity",
    "genre_match_score", "release_recency", "cf_score", "cb_score",
    "trending_score", "session_score",
]


class LtrRanker:
    def __init__(self):
        self.model: Optional[lgb.Booster] = None

    def fit(self, X: np.ndarray, y: np.ndarray, groups: list[int], num_boost_round: int = 100) -> None:
        train = lgb.Dataset(X, label=y, group=groups, feature_name=FEATURE_NAMES)
        params = {
            "objective": "lambdarank",
            "metric": "ndcg",
            "ndcg_eval_at": [5, 10, 20],
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 5,
            "verbose": -1,
        }
        self.model = lgb.train(params, train, num_boost_round=num_boost_round)

    def score(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            return np.zeros(len(X))
        return self.model.predict(X)

    def score_candidates(self, user_features: dict, item_features: list[dict]) -> list[tuple[int, float]]:
        if not item_features:
            return []
        rows = []
        for itf in item_features:
            merged = {**user_features, **itf}
            rows.append([merged.get(f, 0.0) for f in FEATURE_NAMES])
        X = np.array(rows, dtype=np.float32)
        scores = self.score(X)
        return sorted(enumerate(scores.tolist()), key=lambda t: t[1], reverse=True)

    def save(self, path: str) -> None:
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            self.model.save_model(path)

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        self.model = lgb.Booster(model_file=path)
        return True
