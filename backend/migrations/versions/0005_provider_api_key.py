"""Add api_key_enc column to ai_providers

Revision ID: 0005_provider_api_key
Revises: 0004_add_indexes
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_provider_api_key"
down_revision: Union[str, None] = "0004_add_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_providers", sa.Column("api_key_enc", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_providers", "api_key_enc")
