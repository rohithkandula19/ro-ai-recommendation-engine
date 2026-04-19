import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WatchHistory(Base):
    __tablename__ = "watch_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content.id", ondelete="CASCADE"), primary_key=True
    )
    watch_pct: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    total_seconds_watched: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    last_watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    watch_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
