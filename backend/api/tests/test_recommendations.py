import pytest

from schemas.recommendation import RecommendationResponse, RecommendationItem
from datetime import datetime, timezone
import uuid


def test_recommendation_response_shape():
    r = RecommendationResponse(
        surface="home",
        items=[
            RecommendationItem(
                id=uuid.uuid4(), title="T", type="movie",
                match_score=0.8, reason_text="because",
                genre_ids=[1, 2],
            ),
        ],
        generated_at=datetime.now(timezone.utc),
        model_version="v1",
    )
    assert r.surface == "home"
    assert len(r.items) == 1
    assert 0 <= r.items[0].match_score <= 1


@pytest.mark.asyncio
async def test_recommendations_unauthenticated(client):
    r = await client.get("/recommendations/home")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_recommendations_invalid_surface(client):
    r = await client.get("/recommendations/bogus")
    assert r.status_code in (400, 401)
