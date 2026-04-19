import pytest


@pytest.mark.asyncio
async def test_register_login_invalid(client):
    r = await client.post("/auth/login", json={"email": "nope@x.com", "password": "badpass123"})
    assert r.status_code in (401, 500)


@pytest.mark.asyncio
async def test_register_validation(client):
    r = await client.post("/auth/register", json={"email": "bad", "password": "x", "display_name": ""})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_refresh_invalid(client):
    r = await client.post("/auth/refresh", json={"refresh_token": "notatoken"})
    assert r.status_code in (401, 500)
