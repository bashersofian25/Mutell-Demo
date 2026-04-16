"""Add tags to slots and new evaluation fields

Revision ID: 0008_tags_and_metrics
Revises: 0007_nullable_apikey
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008_tags_and_metrics"
down_revision: Union[str, None] = "0008_concurrent_eval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("slots", sa.Column("tags", JSONB, nullable=False, server_default="[]"))

    op.add_column("evaluations", sa.Column("unavailable_items", sa.ARRAY(sa.Text()), nullable=True))
    op.add_column("evaluations", sa.Column("swearing_count", sa.Integer(), nullable=True))
    op.add_column("evaluations", sa.Column("swearing_instances", sa.ARRAY(sa.Text()), nullable=True))
    op.add_column("evaluations", sa.Column("off_topic_count", sa.Integer(), nullable=True))
    op.add_column("evaluations", sa.Column("off_topic_segments", sa.ARRAY(sa.Text()), nullable=True))
    op.add_column("evaluations", sa.Column("speaker_segments", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("evaluations", "speaker_segments")
    op.drop_column("evaluations", "off_topic_segments")
    op.drop_column("evaluations", "off_topic_count")
    op.drop_column("evaluations", "swearing_instances")
    op.drop_column("evaluations", "swearing_count")
    op.drop_column("evaluations", "unavailable_items")
    op.drop_column("slots", "tags")
