"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscription_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
    )

    op.create_table(
        "content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("genre_ids", postgresql.ARRAY(sa.Integer), nullable=False, server_default="{}"),
        sa.Column("release_year", sa.Integer, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("language", sa.String(8), nullable=True),
        sa.Column("maturity_rating", sa.String(10), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("trailer_url", sa.String(500), nullable=True),
        sa.Column("cast_names", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("director", sa.String(255), nullable=True),
        sa.Column("embedding_id", sa.Integer, nullable=True),
        sa.Column("popularity_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_content_type", "content", ["type"])
    op.create_index("ix_content_release_year", "content", ["release_year"])
    op.create_index("ix_content_popularity", "content", ["popularity_score"])
    op.create_index("ix_content_genre_ids", "content", ["genre_ids"], postgresql_using="gin")

    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_ids", postgresql.ARRAY(sa.Integer), nullable=False, server_default="{}"),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("maturity_rating", sa.String(10), nullable=False, server_default="PG-13"),
        sa.Column("onboarding_complete", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.execute("""
        CREATE TABLE interactions (
            id BIGSERIAL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
            event_type VARCHAR(30) NOT NULL,
            value DOUBLE PRECISION,
            session_id UUID,
            device_type VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
    """)
    op.execute("""
        CREATE TABLE interactions_default PARTITION OF interactions DEFAULT;
    """)
    op.execute("CREATE INDEX ix_interactions_user_created ON interactions (user_id, created_at DESC)")
    op.execute("CREATE INDEX ix_interactions_content_event ON interactions (content_id, event_type, created_at)")

    op.create_table(
        "watch_history",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("watch_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("total_seconds_watched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("last_watched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("watch_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_watch_history_last_watched", "watch_history", ["user_id", "last_watched_at"])

    op.create_table(
        "ratings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("rated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_ratings_range"),
    )

    op.create_table(
        "watchlist",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "recommendation_snapshots",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("surface", sa.String(40), primary_key=True),
        sa.Column("content_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("scores", postgresql.ARRAY(sa.Float), nullable=False, server_default="{}"),
        sa.Column("model_version", sa.String(40), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recommendation_snapshots")
    op.drop_table("watchlist")
    op.drop_table("ratings")
    op.drop_index("ix_watch_history_last_watched", table_name="watch_history")
    op.drop_table("watch_history")
    op.execute("DROP TABLE IF EXISTS interactions CASCADE")
    op.drop_table("user_preferences")
    op.drop_table("content")
    op.drop_table("genres")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
