"""unique features: vibe/mood/completion on content, taste_dna on users

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


VIBE_DIMS = ("pace", "emotion", "darkness", "humor", "complexity", "spectacle")


def upgrade() -> None:
    for dim in VIBE_DIMS:
        op.add_column("content", sa.Column(f"vibe_{dim}", sa.Float, nullable=False, server_default="0.5"))
    op.add_column("content", sa.Column("mood_chill_tense", sa.Float, nullable=False, server_default="0.5"))
    op.add_column("content", sa.Column("mood_light_thoughtful", sa.Float, nullable=False, server_default="0.5"))
    op.add_column("content", sa.Column("completion_rate", sa.Float, nullable=False, server_default="0.5"))
    op.create_index("ix_content_mood", "content", ["mood_chill_tense", "mood_light_thoughtful"])

    for dim in VIBE_DIMS:
        op.add_column("users", sa.Column(f"dna_{dim}", sa.Float, nullable=False, server_default="0.5"))
    op.add_column("users", sa.Column("dna_samples", sa.Integer, nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "dna_samples")
    for dim in VIBE_DIMS:
        op.drop_column("users", f"dna_{dim}")
    op.drop_index("ix_content_mood", table_name="content")
    op.drop_column("content", "completion_rate")
    op.drop_column("content", "mood_light_thoughtful")
    op.drop_column("content", "mood_chill_tense")
    for dim in VIBE_DIMS:
        op.drop_column("content", f"vibe_{dim}")
