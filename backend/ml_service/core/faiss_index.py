import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from loguru import logger


class FaissIndex:
    def __init__(self, dim: int = 384, nlist: int = 100, m: int = 8):
        self.dim = dim
        self.nlist = nlist
        self.m = m
        self.index: Optional[faiss.Index] = None
        self.id_map: list[str] = []

    def build(self, embeddings: np.ndarray, ids: list[str]) -> None:
        n = embeddings.shape[0]
        assert embeddings.shape[1] == self.dim, f"expected dim {self.dim}, got {embeddings.shape[1]}"
        faiss.normalize_L2(embeddings)
        if n >= max(self.nlist * 40, 200):
            quantizer = faiss.IndexFlatIP(self.dim)
            self.index = faiss.IndexIVFPQ(quantizer, self.dim, self.nlist, self.m, 8)
            self.index.train(embeddings)
            self.index.add(embeddings)
            self.index.nprobe = 10
        else:
            logger.info(f"Dataset small ({n}), using IndexFlatIP instead of IVFPQ")
            self.index = faiss.IndexFlatIP(self.dim)
            self.index.add(embeddings)
        self.id_map = list(ids)

    def search(self, query: np.ndarray, k: int = 20) -> list[tuple[str, float]]:
        if self.index is None or not self.id_map:
            return []
        if query.ndim == 1:
            query = query.reshape(1, -1)
        q = query.astype(np.float32).copy()
        faiss.normalize_L2(q)
        scores, idxs = self.index.search(q, min(k, len(self.id_map)))
        results = []
        for i, s in zip(idxs[0], scores[0]):
            if 0 <= i < len(self.id_map):
                results.append((self.id_map[int(i)], float(s)))
        return results

    def save(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "faiss.index"))
        with open(os.path.join(path, "id_map.txt"), "w") as f:
            f.write("\n".join(self.id_map))

    def load(self, path: str) -> bool:
        idx_path = os.path.join(path, "faiss.index")
        map_path = os.path.join(path, "id_map.txt")
        if not (os.path.exists(idx_path) and os.path.exists(map_path)):
            return False
        self.index = faiss.read_index(idx_path)
        with open(map_path) as f:
            self.id_map = [line.strip() for line in f if line.strip()]
        return True
