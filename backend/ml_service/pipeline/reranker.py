from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from core.faiss_index import FaissIndex


class Reranker:
    def __init__(self, faiss_index: Optional[FaissIndex], lambda_: float = 0.7):
        self.faiss_index = faiss_index
        self.lambda_ = lambda_

    def _vec(self, cid: str) -> Optional[np.ndarray]:
        if self.faiss_index is None or self.faiss_index.index is None:
            return None
        if cid not in self.faiss_index.id_map:
            return None
        try:
            idx = self.faiss_index.id_map.index(cid)
            return self.faiss_index.index.reconstruct(idx)
        except Exception:
            return None

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def mmr(self, candidates: list[dict], n: int) -> list[dict]:
        if len(candidates) <= 1:
            return candidates[:n]
        selected: list[dict] = []
        selected_vecs: list[np.ndarray] = []
        pool = list(candidates)
        while pool and len(selected) < n:
            best, best_score = None, -1e9
            for c in pool:
                rel = c.get("ranker_score", c.get("score", 0.0))
                v = self._vec(c["content_id"])
                if v is None or not selected_vecs:
                    sim = 0.0
                else:
                    sim = max(self._cosine(v, sv) for sv in selected_vecs)
                mmr_score = self.lambda_ * rel - (1 - self.lambda_) * sim
                if mmr_score > best_score:
                    best, best_score = c, mmr_score
            selected.append(best)
            pool.remove(best)
            bv = self._vec(best["content_id"])
            if bv is not None:
                selected_vecs.append(bv)
        return selected

    def apply_business_rules(
        self,
        items: list[dict],
        seen_ids: set[str],
        content_by_id: dict[str, dict],
        user_maturity: str = "R",
        boost_new_days: int = 14,
    ) -> list[dict]:
        maturity_order = ["G", "PG", "PG-13", "R", "NC-17", "TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]
        try:
            max_idx = maturity_order.index(user_maturity)
        except ValueError:
            max_idx = len(maturity_order) - 1
        allowed = set(maturity_order[: max_idx + 1])
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=boost_new_days)

        filtered = []
        for it in items:
            if it["content_id"] in seen_ids:
                continue
            meta = content_by_id.get(it["content_id"])
            if not meta:
                filtered.append(it)
                continue
            if meta.get("maturity_rating") and meta["maturity_rating"] not in allowed:
                continue
            created = meta.get("created_at")
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    created = None
            if isinstance(created, datetime) and created > cutoff:
                it["ranker_score"] = it.get("ranker_score", it.get("score", 0.0)) * 1.15
            filtered.append(it)
        return filtered

    def rerank(
        self,
        candidates: list[dict],
        n: int,
        seen_ids: set[str],
        content_by_id: dict[str, dict],
        user_maturity: str = "R",
    ) -> list[dict]:
        filtered = self.apply_business_rules(candidates, seen_ids, content_by_id, user_maturity)
        return self.mmr(filtered, n)
