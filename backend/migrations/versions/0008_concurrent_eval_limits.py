"""Add max_concurrent_evaluations to plans and tenants

Revision ID: 0008_concurrent_eval
Revises: 0007_nullable_apikey
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_concurrent_eval"
down_revision: Union[str, None] = "0007_nullable_apikey"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "plans",
        sa.Column("max_concurrent_evaluations", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "tenants",
        sa.Column("max_concurrent_evaluations", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "max_concurrent_evaluations")
    op.drop_column("plans", "max_concurrent_evaluations")
