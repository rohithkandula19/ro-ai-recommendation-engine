import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


VALID_EVENT_TYPES = {
    "click", "play", "pause", "progress", "complete",
    "like", "dislike", "search", "add_to_list", "rate", "skip",
}


class EventIn(BaseModel):
    user_id: uuid.UUID
    content_id: uuid.UUID | None = None
    event_type: str
    value: float | None = None
    session_id: uuid.UUID | None = None
    device_type: str | None = Field(default=None, max_length=20)
    timestamp: datetime | None = None

    @field_validator("event_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {sorted(VALID_EVENT_TYPES)}")
        return v


class EventBatch(BaseModel):
    events: list[EventIn] = Field(min_length=1, max_length=500)


class EventIngestResponse(BaseModel):
    accepted: int
    rejected: int
