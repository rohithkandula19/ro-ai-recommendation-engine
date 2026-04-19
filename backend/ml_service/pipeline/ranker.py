from typing import Optional

import numpy as np

from models.ranking_model import LtrRanker, FEATURE_NAMES


class Ranker:
    def __init__(self, ltr: Optional[LtrRanker] = None):
        self.ltr = ltr

    def rank(
        self,
        candidates: list[dict],
        user_features: dict,
        item_features_list: list[dict],
        blend_alpha: float = 0.6,
    ) -> list[dict]:
        if not candidates:
            return []
        if self.ltr is None or self.ltr.model is None:
            for c, itf in zip(candidates, item_features_list):
                c["ranker_score"] = float(c.get("score", 0.0))
            candidates.sort(key=lambda d: d["ranker_score"], reverse=True)
            return candidates

        rows = []
        for itf in item_features_list:
            merged = {**user_features, **itf}
            rows.append([merged.get(f, 0.0) for f in FEATURE_NAMES])
        X = np.array(rows, dtype=np.float32)
        scores = self.ltr.score(X)
        max_s = float(np.max(scores)) if len(scores) else 1.0
        min_s = float(np.min(scores)) if len(scores) else 0.0
        rng = (max_s - min_s) or 1.0
        for c, s in zip(candidates, scores):
            norm_ltr = (float(s) - min_s) / rng
            c["ranker_score"] = blend_alpha * norm_ltr + (1 - blend_alpha) * float(c.get("score", 0.0))
        candidates.sort(key=lambda d: d["ranker_score"], reverse=True)
        return candidates
