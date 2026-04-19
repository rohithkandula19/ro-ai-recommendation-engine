"""Mega-50: audit, sso, 2fa, streaks, dms, feed, stripe, imports, webhooks, franchises

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Audit
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=True),
        sa.Column("target_id", sa.String(120), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_actor", "audit_events", ["actor_id", "created_at"])

    # 2FA / TOTP
    op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("totp_verified", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("oauth_provider", sa.String(30), nullable=True))
    op.add_column("users", sa.Column("oauth_sub", sa.String(120), nullable=True))
    op.create_index("ix_users_oauth", "users", ["oauth_provider", "oauth_sub"])

    # Streaks
    op.create_table(
        "user_streaks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("current_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("best_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date, nullable=True),
        sa.Column("badges", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
    )

    # DMs
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("attached_content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="SET NULL"), nullable=True),
        sa.Column("read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_messages_pair", "messages", ["sender_id", "recipient_id", "created_at"])

    # Social activity feed
    op.create_table(
        "activity_feed",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),  # rated, completed, reviewed, created_collection
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_activity_user", "activity_feed", ["user_id", "created_at"])

    # Webhook subscriptions
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("secret", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Imports (Letterboxd/Trakt CSV)
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("rows_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rows_matched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Push subscriptions
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.String(1000), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(200), nullable=False),
        sa.Column("auth", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Ranker variants (A/B)
    op.create_table(
        "ranker_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(60), nullable=False, unique=True),
        sa.Column("artifact_path", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("ndcg_at_10", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # Franchises
    op.create_table(
        "franchises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
    )
    op.add_column("content", sa.Column("franchise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("franchises.id", ondelete="SET NULL"), nullable=True))

    # Streaming availability
    op.create_table(
        "streaming_availability",
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("service", sa.String(40), primary_key=True),  # netflix, prime, hbo, hulu, etc.
        sa.Column("region", sa.String(5), primary_key=True, server_default="US"),
        sa.Column("deep_link", sa.String(500), nullable=True),
    )

    # Awards denormalized string
    op.add_column("content", sa.Column("awards", sa.String(500), nullable=True))
    op.add_column("content", sa.Column("imdb_rating", sa.Float, nullable=True))
    op.add_column("content", sa.Column("rt_score", sa.Integer, nullable=True))

    # Feature flags
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("rollout_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    for t in ("feature_flags", "streaming_availability", "franchises",
              "ranker_variants", "push_subscriptions", "import_jobs",
              "webhook_subscriptions", "activity_feed", "messages",
              "user_streaks", "audit_events"):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for col in ("awards", "imdb_rating", "rt_score", "franchise_id"):
        op.execute(f"ALTER TABLE content DROP COLUMN IF EXISTS {col}")
    for col in ("totp_secret", "totp_verified", "oauth_provider", "oauth_sub"):
        op.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}")
