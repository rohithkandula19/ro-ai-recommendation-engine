"""Recommendation quality metrics — NDCG, Precision, Recall, MAP at K."""
import math
from typing import Iterable


def precision_at_k(recommended: list[str], relevant: Iterable[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = recommended[:k]
    rel_set = set(relevant)
    hits = sum(1 for r in top if r in rel_set)
    return hits / k


def recall_at_k(recommended: list[str], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    if not rel_set:
        return 0.0
    top = set(recommended[:k])
    return len(top & rel_set) / len(rel_set)


def dcg(gains: list[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(recommended: list[str], relevance_map: dict[str, float], k: int) -> float:
    if k <= 0:
        return 0.0
    actual = [float(relevance_map.get(r, 0.0)) for r in recommended[:k]]
    ideal = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = dcg(ideal)
    if idcg == 0:
        return 0.0
    return dcg(actual) / idcg


def map_at_k(recommended: list[str], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    if not rel_set or k <= 0:
        return 0.0
    score = 0.0
    hits = 0
    for i, r in enumerate(recommended[:k]):
        if r in rel_set:
            hits += 1
            score += hits / (i + 1)
    return score / min(len(rel_set), k)


def evaluate_all(
    test_user_recs: dict[str, list[str]],
    test_user_relevant: dict[str, list[str]],
    k: int = 10,
    relevance_map: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    ps, rs, ns, ms = [], [], [], []
    for user, recs in test_user_recs.items():
        rel = test_user_relevant.get(user, [])
        ps.append(precision_at_k(recs, rel, k))
        rs.append(recall_at_k(recs, rel, k))
        rm = (relevance_map or {}).get(user) or {r: 1.0 for r in rel}
        ns.append(ndcg_at_k(recs, rm, k))
        ms.append(map_at_k(recs, rel, k))

    def mean(xs): return sum(xs) / len(xs) if xs else 0.0
    return {
        f"precision@{k}": mean(ps),
        f"recall@{k}": mean(rs),
        f"ndcg@{k}": mean(ns),
        f"map@{k}": mean(ms),
    }


if __name__ == "__main__":
    test_recs = {"u1": ["a", "b", "c", "d"], "u2": ["x", "y", "z"]}
    test_rel = {"u1": ["a", "c"], "u2": ["y"]}
    print(evaluate_all(test_recs, test_rel, k=3))
