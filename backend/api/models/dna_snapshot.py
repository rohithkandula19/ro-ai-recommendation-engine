import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserDNASnapshot(Base):
    __tablename__ = "user_dna_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, primary_key=True)
    dna_pace: Mapped[float] = mapped_column(Float, nullable=False)
    dna_emotion: Mapped[float] = mapped_column(Float, nullable=False)
    dna_darkness: Mapped[float] = mapped_column(Float, nullable=False)
    dna_humor: Mapped[float] = mapped_column(Float, nullable=False)
    dna_complexity: Mapped[float] = mapped_column(Float, nullable=False)
    dna_spectacle: Mapped[float] = mapped_column(Float, nullable=False)
    samples: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
