"""chat_feedback + user_chat_profile

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_feedback",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("user_message", sa.Text, nullable=True),
        sa.Column("assistant_message", sa.Text, nullable=False),
        sa.Column("feedback", sa.Integer, nullable=False),
        sa.Column("mentioned_content_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
                  nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("feedback IN (-1, 1)", name="ck_chat_feedback_range"),
    )
    op.create_index("ix_chat_feedback_user", "chat_feedback", ["user_id", "created_at"])

    op.create_table(
        "user_chat_profile",
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("preferred_tone", sa.String(40), nullable=False, server_default="friendly"),
        sa.Column("preferred_reply_length", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("custom_system_note", sa.String(500), nullable=True),
        sa.Column("positive_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("negative_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_chat_profile")
    op.drop_index("ix_chat_feedback_user", table_name="chat_feedback")
    op.drop_table("chat_feedback")
