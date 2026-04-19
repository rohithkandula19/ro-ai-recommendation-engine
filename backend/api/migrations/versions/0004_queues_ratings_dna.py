"""queues + mood-tagged ratings + dna snapshots

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watch_queues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("icon", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_queues_user_name"),
    )
    op.create_index("ix_queues_user", "watch_queues", ["user_id"])

    op.create_table(
        "queue_items",
        sa.Column("queue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watch_queues.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.add_column("ratings", sa.Column("mood_tag", sa.String(40), nullable=True))
    op.add_column("ratings", sa.Column("note", sa.String(500), nullable=True))

    op.create_table(
        "user_dna_snapshots",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("snapshot_date", sa.Date, primary_key=True),
        sa.Column("dna_pace", sa.Float, nullable=False),
        sa.Column("dna_emotion", sa.Float, nullable=False),
        sa.Column("dna_darkness", sa.Float, nullable=False),
        sa.Column("dna_humor", sa.Float, nullable=False),
        sa.Column("dna_complexity", sa.Float, nullable=False),
        sa.Column("dna_spectacle", sa.Float, nullable=False),
        sa.Column("samples", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("user_dna_snapshots")
    op.drop_column("ratings", "note")
    op.drop_column("ratings", "mood_tag")
    op.drop_table("queue_items")
    op.drop_index("ix_queues_user", table_name="watch_queues")
    op.drop_table("watch_queues")
