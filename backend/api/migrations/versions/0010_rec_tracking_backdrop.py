"""Add backdrop_url + youtube_trailer_id to content.

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content", sa.Column("backdrop_url", sa.String(500), nullable=True))
    op.add_column("content", sa.Column("youtube_trailer_id", sa.String(30), nullable=True))
    # Backfill YouTube IDs where trailer_url contains a youtube link.
    # Use DO block to avoid any SQLAlchemy param interpolation.
    op.execute("""
        DO $$
        BEGIN
          UPDATE content
          SET youtube_trailer_id = substring(trailer_url FROM '([A-Za-z0-9_-]{11})')
          WHERE trailer_url LIKE '%youtube.com/watch?v=%'
             OR trailer_url LIKE '%youtu.be/%';
        END $$;
    """)


def downgrade() -> None:
    op.drop_column("content", "youtube_trailer_id")
    op.drop_column("content", "backdrop_url")
