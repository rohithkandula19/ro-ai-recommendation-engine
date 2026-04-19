from pipeline.reranker import Reranker


def test_removes_seen_and_respects_n():
    r = Reranker(faiss_index=None, lambda_=0.7)
    cands = [
        {"content_id": "a", "score": 0.9, "ranker_score": 0.9},
        {"content_id": "b", "score": 0.8, "ranker_score": 0.8},
        {"content_id": "c", "score": 0.7, "ranker_score": 0.7},
    ]
    out = r.rerank(cands, n=2, seen_ids={"a"}, content_by_id={}, user_maturity="R")
    ids = [x["content_id"] for x in out]
    assert "a" not in ids
    assert len(out) == 2
