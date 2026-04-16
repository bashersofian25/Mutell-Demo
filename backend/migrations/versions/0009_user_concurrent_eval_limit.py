"""Add max_concurrent_evaluations to users

Revision ID: 0009_user_concurrent_eval
Revises: 0008_tags_and_metrics
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_user_concurrent_eval"
down_revision: Union[str, None] = "0008_tags_and_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("max_concurrent_evaluations", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("users", "max_concurrent_evaluations")
