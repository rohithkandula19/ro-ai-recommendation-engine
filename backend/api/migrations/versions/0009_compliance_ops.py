"""Compliance + business ops: cookies/consent, geo, blocklist, gift codes, affiliates

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consent_records",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("analytics", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("marketing", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("personalization", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("age_confirmed_over", sa.Integer, nullable=False, server_default="13"),
        sa.Column("region", sa.String(5), nullable=False, server_default="US"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_regions",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("allowed_regions", postgresql.ARRAY(sa.String), nullable=False, server_default="{US,GB,CA,AU,EU}"),
    )

    op.create_table(
        "user_blocks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("blocked_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "gift_codes",
        sa.Column("code", sa.String(20), primary_key=True),
        sa.Column("purchaser_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("redeemer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tier", sa.String(20), nullable=False, server_default="pro"),
        sa.Column("months", sa.Integer, nullable=False, server_default="1"),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "affiliate_links",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("service", sa.String(40), primary_key=True),
        sa.Column("link", sa.String(500), nullable=False),
        sa.Column("commission_bps", sa.Integer, nullable=False, server_default="300"),  # 3.00%
    )

    op.create_table(
        "review_reactions",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("emoji", sa.String(10), nullable=False),
    )

    op.create_table(
        "content_availability_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
        sa.Column("region", sa.String(5), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("clicked_service", sa.String(40), nullable=False),
        sa.Column("affiliate_revenue_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    for t in ("content_availability_log", "review_reactions", "affiliate_links",
              "gift_codes", "user_blocks", "content_regions", "consent_records"):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
