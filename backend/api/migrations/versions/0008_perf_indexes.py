"""Perf indexes + moderation + newsletter + referrals

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Perf indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_watch_history_user ON watch_history (user_id, last_watched_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ratings_user_rated ON ratings (user_id, rated_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_mood_pop ON content (popularity_score DESC, mood_chill_tense, mood_light_thoughtful)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_title_lower ON content (lower(title))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_dna_samples ON users (dna_samples DESC) WHERE dna_samples > 0")

    # Moderation
    op.create_table(
        "moderation_flags",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("target_type", sa.String(40), nullable=False),  # review, comment, user
        sa.Column("target_id", sa.String(80), nullable=False),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.String(300), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Newsletter
    op.create_table(
        "newsletter_subscribers",
        sa.Column("email", sa.String(255), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("unsubscribed", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    # Referrals
    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("referrer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("uses", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "referral_redemptions",
        sa.Column("code", sa.String(20), sa.ForeignKey("referrals.code", ondelete="CASCADE"), primary_key=True),
        sa.Column("redeemer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Rec quality tracking
    op.create_table(
        "rec_quality_daily",
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("surface", sa.String(40), primary_key=True),
        sa.Column("impressions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("plays", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dislikes", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    for t in ("rec_quality_daily", "referral_redemptions", "referrals",
              "newsletter_subscribers", "moderation_flags"):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
