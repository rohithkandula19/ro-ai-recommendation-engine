import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free", server_default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    dna_pace: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_emotion: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_darkness: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_humor: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_complexity: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_spectacle: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    dna_samples: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    preferences: Mapped["UserPreferences"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    genre_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list, server_default="{}")
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", server_default="en")
    maturity_rating: Mapped[str] = mapped_column(String(10), default="PG-13", server_default="PG-13")
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="preferences")
