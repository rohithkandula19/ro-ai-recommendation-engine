import asyncio
from typing import Optional

from loguru import logger

from core.faiss_index import FaissIndex
from models.als_model import ALSRecommender


class CandidateGenerator:
    def __init__(
        self,
        als: Optional[ALSRecommender],
        faiss_index: Optional[FaissIndex],
        redis_client,
    ):
        self.als = als
        self.faiss_index = faiss_index
        self.redis = redis_client

    async def _cf(self, user_id: str, k: int) -> list[tuple[str, float, str]]:
        if self.als is None:
            return []
        try:
            items = self.als.recommend(user_id, n=k)
            return [(cid, score, "cf") for cid, score in items]
        except Exception as e:
            logger.warning(f"cf candidates failed: {e}")
            return []

    async def _cb(self, top_watched: list[str], k: int) -> list[tuple[str, float, str]]:
        if self.faiss_index is None or not top_watched:
            return []
        try:
            import numpy as np
            results: dict[str, float] = {}
            for cid in top_watched[:5]:
                if cid in self.faiss_index.id_map:
                    idx = self.faiss_index.id_map.index(cid)
                    try:
                        vec = self.faiss_index.index.reconstruct(idx)
                    except Exception:
                        continue
                    for nid, s in self.faiss_index.search(np.array(vec), k=k // 5):
                        if nid != cid:
                            results[nid] = max(results.get(nid, 0), s)
            return [(cid, s, "cb") for cid, s in results.items()]
        except Exception as e:
            logger.warning(f"cb candidates failed: {e}")
            return []

    async def _trending(self, k: int) -> list[tuple[str, float, str]]:
        if self.redis is None:
            return []
        try:
            entries = await self.redis.zrevrange("trending:global", 0, k - 1, withscores=True)
            if not entries:
                return []
            max_score = max(s for _, s in entries) or 1.0
            return [(cid, float(s) / max_score, "trending") for cid, s in entries]
        except Exception as e:
            logger.warning(f"trending candidates failed: {e}")
            return []

    async def _session(self, session_items: list[str], k: int) -> list[tuple[str, float, str]]:
        if self.faiss_index is None or not session_items:
            return []
        try:
            import numpy as np
            results: dict[str, float] = {}
            for cid in session_items[-5:]:
                if cid in self.faiss_index.id_map:
                    idx = self.faiss_index.id_map.index(cid)
                    try:
                        vec = self.faiss_index.index.reconstruct(idx)
                    except Exception:
                        continue
                    for nid, s in self.faiss_index.search(np.array(vec), k=k // 5):
                        if nid != cid:
                            results[nid] = max(results.get(nid, 0), s * 0.9)
            return [(cid, s, "session") for cid, s in results.items()]
        except Exception as e:
            logger.warning(f"session candidates failed: {e}")
            return []

    async def generate(
        self,
        user_id: str,
        top_watched: list[str],
        session_items: list[str],
        k: int = 500,
    ) -> list[dict]:
        cf, cb, tr, ss = await asyncio.gather(
            self._cf(user_id, k),
            self._cb(top_watched, k // 2),
            self._trending(k // 4),
            self._session(session_items, k // 4),
            return_exceptions=False,
        )
        merged: dict[str, dict] = {}
        for batch, src in [(cf, "cf"), (cb, "cb"), (tr, "trending"), (ss, "session")]:
            for cid, score, _ in batch:
                if cid not in merged:
                    merged[cid] = {"content_id": cid, "score": 0.0, "sources": []}
                merged[cid]["score"] = max(merged[cid]["score"], float(score))
                if src not in merged[cid]["sources"]:
                    merged[cid]["sources"].append(src)
        out = sorted(merged.values(), key=lambda d: d["score"], reverse=True)
        return out[:k]
