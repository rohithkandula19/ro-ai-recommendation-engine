import pytest
import uuid
from schemas.event import EventIn, EventBatch


def test_event_validates_type():
    with pytest.raises(Exception):
        EventIn(user_id=uuid.uuid4(), event_type="not_a_real_event")


def test_event_batch_min_length():
    with pytest.raises(Exception):
        EventBatch(events=[])


def test_event_batch_accepts_valid():
    b = EventBatch(events=[EventIn(user_id=uuid.uuid4(), event_type="click")])
    assert len(b.events) == 1


@pytest.mark.asyncio
async def test_ingest_requires_auth(client):
    r = await client.post("/events/ingest", json={"events": [{"user_id": str(uuid.uuid4()), "event_type": "click"}]})
    assert r.status_code == 401
