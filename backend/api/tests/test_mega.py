import pytest


@pytest.mark.asyncio
async def test_semantic_search_shape(client):
    r = await client.post("/search/semantic", json={"query": "test", "limit": 3})
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_ai_collection_validation(client):
    r = await client.post("/ai-collections", json={"name": "", "prompt": "x"})
    assert r.status_code in (401, 422)


@pytest.mark.asyncio
async def test_leaderboards(client):
    r = await client.get("/leaderboards/top-raters")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_health_live_ready(client):
    r = await client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "live"}


@pytest.mark.asyncio
async def test_search_suggest_requires_q(client):
    r = await client.get("/search/suggest")
    assert r.status_code in (422, 401)


@pytest.mark.asyncio
async def test_batch_recs_validates(client):
    r = await client.post("/recommendations/batch", json={"surfaces": []})
    assert r.status_code in (422, 401)


@pytest.mark.asyncio
async def test_referral_create_requires_auth(client):
    r = await client.post("/referrals/create")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_newsletter_subscribe_email_validation(client):
    r = await client.post("/newsletter/subscribe", json={"email": "bad"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_watch_party_create_auth(client):
    r = await client.post("/watch-parties", json={"content_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code in (401, 404)


@pytest.mark.asyncio
async def test_2fa_setup_auth(client):
    r = await client.post("/auth/2fa/setup")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_gdpr_delete_requires_confirm(client):
    r = await client.post("/users/me/delete", json={"confirm": "wrong"})
    assert r.status_code in (400, 401)
