"""Avro-compatible event schema definitions."""
import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator


VALID_EVENT_TYPES = {
    "click", "play", "pause", "progress", "complete",
    "like", "dislike", "search", "add_to_list", "rate", "skip",
}


class Event(BaseModel):
    user_id: uuid.UUID
    content_id: uuid.UUID | None = None
    event_type: str
    value: float | None = None
    session_id: uuid.UUID | None = None
    device_type: str | None = None
    timestamp: datetime | None = None

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"invalid event_type: {v}")
        return v


EVENT_AVRO_SCHEMA = {
    "type": "record",
    "name": "UserEvent",
    "namespace": "ro.rec.events",
    "fields": [
        {"name": "user_id", "type": "string"},
        {"name": "content_id", "type": ["null", "string"], "default": None},
        {"name": "event_type", "type": "string"},
        {"name": "value", "type": ["null", "double"], "default": None},
        {"name": "session_id", "type": ["null", "string"], "default": None},
        {"name": "device_type", "type": ["null", "string"], "default": None},
        {"name": "timestamp", "type": ["null", "string"], "default": None},
    ],
}
