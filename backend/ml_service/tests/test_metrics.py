from evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k, map_at_k


def test_precision_at_k():
    assert precision_at_k(["a", "b", "c"], {"a", "c"}, 3) == 2 / 3


def test_recall_at_k():
    assert recall_at_k(["a", "b", "c"], {"a", "c", "z"}, 3) == 2 / 3


def test_ndcg_perfect():
    rel = {"a": 3.0, "b": 2.0, "c": 1.0}
    assert abs(ndcg_at_k(["a", "b", "c"], rel, 3) - 1.0) < 1e-9


def test_ndcg_worst():
    rel = {"a": 3.0, "b": 2.0, "c": 1.0}
    val = ndcg_at_k(["c", "b", "a"], rel, 3)
    assert 0 < val < 1


def test_map():
    assert abs(map_at_k(["a", "x", "b"], {"a", "b"}, 3) - ((1 / 1 + 2 / 3) / 2)) < 1e-9
