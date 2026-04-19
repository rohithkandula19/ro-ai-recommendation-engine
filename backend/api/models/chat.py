import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"
    __table_args__ = (CheckConstraint("feedback IN (-1, 1)", name="ck_chat_feedback_range"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    user_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    assistant_message: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[int] = mapped_column(Integer, nullable=False)
    mentioned_content_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserChatProfile(Base):
    __tablename__ = "user_chat_profile"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_tone: Mapped[str] = mapped_column(String(40), default="friendly", server_default="friendly")
    preferred_reply_length: Mapped[str] = mapped_column(String(20), default="medium", server_default="medium")
    custom_system_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    positive_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    negative_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
