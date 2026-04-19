import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class Content(Base):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    genre_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list, server_default="{}")
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    maturity_rating: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trailer_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cast_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, server_default="{}")
    director: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vibe_pace: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    vibe_emotion: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    vibe_darkness: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    vibe_humor: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    vibe_complexity: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    vibe_spectacle: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    mood_chill_tense: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    mood_light_thoughtful: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    completion_rate: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
