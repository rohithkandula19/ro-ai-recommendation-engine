import pytest
from pipeline.candidate_generator import CandidateGenerator


class FakeALS:
    def recommend(self, user_id, n=500):
        return [("c1", 0.9), ("c2", 0.7)]


class FakeFAISS:
    def __init__(self):
        self.id_map = []
        self.index = None

    def search(self, vec, k=20):
        return []


class FakeRedis:
    async def zrevrange(self, key, start, end, withscores=False):
        return [("c3", 5.0), ("c4", 2.0)]


@pytest.mark.asyncio
async def test_merges_four_sources():
    cg = CandidateGenerator(FakeALS(), FakeFAISS(), FakeRedis())
    out = await cg.generate("user1", top_watched=[], session_items=[], k=50)
    ids = {c["content_id"] for c in out}
    assert "c1" in ids and "c3" in ids
