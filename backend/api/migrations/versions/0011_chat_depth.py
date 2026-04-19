"""Chat-80: long-term memory, threads, anti-goals, token usage, chat shares

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_facts",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fact", sa.String(500), nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="chat"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_user_facts", "user_facts", ["user_id", "created_at"])

    op.create_table(
        "chat_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False, server_default="New chat"),
        sa.Column("persona", sa.String(40), nullable=False, server_default="friendly"),
        sa.Column("pinned", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("share_token", sa.String(30), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_chat_threads_user", "chat_threads", ["user_id", "updated_at"])

    op.create_table(
        "anti_goals",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("avoid_genres", postgresql.ARRAY(sa.Integer), nullable=False, server_default="{}"),
        sa.Column("avoid_keywords", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("avoid_cast_names", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("max_dnl_darkness", sa.Float, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "llm_usage",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("month", sa.String(7), primary_key=True),  # YYYY-MM
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("calls", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "chat_plugins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("webhook_url", sa.String(500), nullable=False),
        sa.Column("trigger_keywords", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    for t in ("chat_plugins", "llm_usage", "anti_goals", "chat_threads", "user_facts"):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
