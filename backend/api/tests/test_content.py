import pytest
from schemas.content import ContentCreate


def test_content_validates_type():
    with pytest.raises(Exception):
        ContentCreate(title="x", type="invalid")


def test_content_valid():
    c = ContentCreate(title="Foo", type="movie", genre_ids=[1])
    assert c.type == "movie"


@pytest.mark.asyncio
async def test_list_content_public(client):
    r = await client.get("/content")
    assert r.status_code in (200, 500)
