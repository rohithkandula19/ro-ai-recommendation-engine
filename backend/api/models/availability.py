import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ContentAvailability(Base):
    __tablename__ = "content_availability"
    __table_args__ = (UniqueConstraint("content_id", "provider", "offer_type", "region", name="uq_availability"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    offer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    deep_link: Mapped[str] = mapped_column(String(1000), nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    quality: Mapped[str | None] = mapped_column(String(12), nullable=True)
    region: Mapped[str] = mapped_column(String(4), nullable=False, server_default="US")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
