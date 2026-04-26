"""Where-to-watch provider availability (JustWatch / TMDB watch-providers)

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_availability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("provider_logo", sa.String(500), nullable=True),
        sa.Column("offer_type", sa.String(20), nullable=False),
        sa.Column("deep_link", sa.String(1000), nullable=False),
        sa.Column("price", sa.Float, nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("quality", sa.String(12), nullable=True),
        sa.Column("region", sa.String(4), nullable=False, server_default="US"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("content_id", "provider", "offer_type", "region", name="uq_availability"),
    )
    op.create_index("ix_availability_content", "content_availability", ["content_id", "region"])


def downgrade() -> None:
    op.drop_index("ix_availability_content", table_name="content_availability")
    op.drop_table("content_availability")
