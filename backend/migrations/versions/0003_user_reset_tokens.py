"""Add reset_token and reset_expires to users

Revision ID: 0003_user_reset_tokens
Revises: 0002_audit_log
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_user_reset_tokens"
down_revision: Union[str, None] = "0002_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("reset_expires", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "reset_expires")
    op.drop_column("users", "reset_token")
