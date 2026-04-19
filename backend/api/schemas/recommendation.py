import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


VALID_SURFACES = {"home", "trending", "because_you_watched", "continue_watching", "new_releases"}


class RecommendationItem(BaseModel):
    id: uuid.UUID
    title: str
    type: str
    thumbnail_url: str | None = None
    match_score: float = Field(ge=0, le=1)
    reason_text: str
    genre_ids: list[int] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    surface: str
    items: list[RecommendationItem]
    generated_at: datetime
    model_version: str
