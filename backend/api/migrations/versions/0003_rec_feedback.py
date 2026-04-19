"""rec_feedback table for LTR fine-tuning

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rec_feedback",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surface", sa.String(40), nullable=False),
        sa.Column("feedback", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("feedback IN (-1, 0, 1)", name="ck_feedback_range"),
    )
    op.create_index("ix_rec_feedback_user", "rec_feedback", ["user_id", "created_at"])
    op.create_index("ix_rec_feedback_content", "rec_feedback", ["content_id"])


def downgrade() -> None:
    op.drop_index("ix_rec_feedback_content", table_name="rec_feedback")
    op.drop_index("ix_rec_feedback_user", table_name="rec_feedback")
    op.drop_table("rec_feedback")
