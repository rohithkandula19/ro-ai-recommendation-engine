"""Schemas for the unique features: taste DNA, mood, time-budget, why, co-viewer, AI reranker."""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class VibeVector(BaseModel):
    pace: float = Field(ge=0, le=1)
    emotion: float = Field(ge=0, le=1)
    darkness: float = Field(ge=0, le=1)
    humor: float = Field(ge=0, le=1)
    complexity: float = Field(ge=0, le=1)
    spectacle: float = Field(ge=0, le=1)


class TasteDNAResponse(BaseModel):
    user_id: uuid.UUID
    dna: VibeVector
    samples: int


class MoodRecRequest(BaseModel):
    chill_tense: float = Field(ge=0, le=1, default=0.5)
    light_thoughtful: float = Field(ge=0, le=1, default=0.5)
    limit: int = Field(ge=1, le=100, default=20)


class TimeBudgetRequest(BaseModel):
    minutes: int = Field(ge=5, le=480)
    limit: int = Field(ge=1, le=100, default=20)
    tolerance_pct: int = Field(ge=5, le=50, default=20)


class RankerSignal(BaseModel):
    name: str
    value: float = Field(ge=0, le=1)
    description: str


class ExplainResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    content_id: uuid.UUID
    signals: list[RankerSignal]
    dominant_reason: str
    ai_summary: str | None = None


class CoViewerRequest(BaseModel):
    user_ids: list[uuid.UUID] = Field(min_length=2, max_length=5)
    limit: int = Field(ge=1, le=50, default=20)


class RecFeedbackRequest(BaseModel):
    content_id: uuid.UUID
    surface: str
    feedback: int = Field(ge=-1, le=1)  # -1 dislike, 0 neutral, +1 like
    reason: str | None = Field(default=None, max_length=500)


class NLSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(ge=1, le=50, default=20)


class NLSearchResponse(BaseModel):
    query: str
    parsed_filters: dict
    results: list[dict]
    generated_at: datetime
