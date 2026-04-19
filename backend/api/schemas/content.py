import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_TYPES = {"movie", "series", "short"}


class ContentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: str
    genre_ids: list[int] = Field(default_factory=list)
    release_year: int | None = Field(default=None, ge=1900, le=2100)
    duration_seconds: int | None = Field(default=None, ge=0)
    language: str | None = None
    maturity_rating: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    trailer_url: str | None = None
    cast_names: list[str] = Field(default_factory=list)
    director: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ALLOWED_TYPES:
            raise ValueError(f"type must be one of {sorted(ALLOWED_TYPES)}")
        return v


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    trailer_url: str | None = None
    is_active: bool | None = None


class ContentOut(ContentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    popularity_score: float
    is_active: bool
    created_at: datetime


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str


class SearchResultItem(BaseModel):
    id: uuid.UUID
    title: str
    type: str
    relevance_score: float
    thumbnail_url: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
