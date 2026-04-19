import os
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from implicit.als import AlternatingLeastSquares
from loguru import logger
from scipy.sparse import csr_matrix


class ALSRecommender:
    def __init__(self, factors: int = 64, iterations: int = 15, regularization: float = 0.01):
        self.factors = factors
        self.iterations = iterations
        self.regularization = regularization
        self.model: Optional[AlternatingLeastSquares] = None
        self.user_id_to_idx: dict[str, int] = {}
        self.item_id_to_idx: dict[str, int] = {}
        self.idx_to_item_id: list[str] = []
        self.user_item_matrix: Optional[csr_matrix] = None

    def fit(self, interactions: list[tuple[str, str, float]]) -> None:
        users = sorted({u for u, _, _ in interactions})
        items = sorted({i for _, i, _ in interactions})
        self.user_id_to_idx = {u: i for i, u in enumerate(users)}
        self.item_id_to_idx = {it: i for i, it in enumerate(items)}
        self.idx_to_item_id = items

        rows, cols, data = [], [], []
        for u, it, conf in interactions:
            rows.append(self.user_id_to_idx[u])
            cols.append(self.item_id_to_idx[it])
            data.append(1.0 + 40.0 * float(conf))

        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)), shape=(len(users), len(items)), dtype=np.float32
        )
        self.model = AlternatingLeastSquares(
            factors=self.factors,
            iterations=self.iterations,
            regularization=self.regularization,
            use_gpu=False,
        )
        self.model.fit(self.user_item_matrix, show_progress=False)
        logger.info(f"ALS fit: {len(users)} users, {len(items)} items")

    def recommend(self, user_id: str, n: int = 500) -> list[tuple[str, float]]:
        if self.model is None or user_id not in self.user_id_to_idx:
            return []
        uidx = self.user_id_to_idx[user_id]
        ids, scores = self.model.recommend(
            uidx, self.user_item_matrix[uidx], N=min(n, len(self.idx_to_item_id)), filter_already_liked_items=True,
        )
        return [(self.idx_to_item_id[int(i)], float(s)) for i, s in zip(ids, scores)]

    def save(self, path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)
        if self.model is not None:
            np.save(os.path.join(path, "user_factors.npy"), self.model.user_factors)
            np.save(os.path.join(path, "item_factors.npy"), self.model.item_factors)
        with open(os.path.join(path, "meta.pkl"), "wb") as f:
            pickle.dump({
                "user_id_to_idx": self.user_id_to_idx,
                "item_id_to_idx": self.item_id_to_idx,
                "idx_to_item_id": self.idx_to_item_id,
                "factors": self.factors,
                "iterations": self.iterations,
                "regularization": self.regularization,
            }, f)
        if self.user_item_matrix is not None:
            from scipy.sparse import save_npz
            save_npz(os.path.join(path, "user_item.npz"), self.user_item_matrix)

    def load(self, path: str) -> bool:
        meta_path = os.path.join(path, "meta.pkl")
        uf_path = os.path.join(path, "user_factors.npy")
        if_path = os.path.join(path, "item_factors.npy")
        ui_path = os.path.join(path, "user_item.npz")
        if not all(os.path.exists(p) for p in (meta_path, uf_path, if_path, ui_path)):
            return False
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        self.user_id_to_idx = meta["user_id_to_idx"]
        self.item_id_to_idx = meta["item_id_to_idx"]
        self.idx_to_item_id = meta["idx_to_item_id"]
        self.factors = meta["factors"]
        self.iterations = meta["iterations"]
        self.regularization = meta["regularization"]
        self.model = AlternatingLeastSquares(
            factors=self.factors, iterations=self.iterations, regularization=self.regularization, use_gpu=False,
        )
        self.model.user_factors = np.load(uf_path)
        self.model.item_factors = np.load(if_path)
        from scipy.sparse import load_npz
        self.user_item_matrix = load_npz(ui_path)
        return True
