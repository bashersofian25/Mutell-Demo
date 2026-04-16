"""Add triggered_by_user_id to slots

Revision ID: 0010_slot_triggered_by_user
Revises: 0009_user_concurrent_eval
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_slot_triggered_by_user"
down_revision: Union[str, None] = "0009_user_concurrent_eval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("slots", sa.Column("triggered_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))


def downgrade() -> None:
    op.drop_column("slots", "triggered_by_user_id")
