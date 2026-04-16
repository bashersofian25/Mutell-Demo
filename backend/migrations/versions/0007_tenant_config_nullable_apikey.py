"""Make tenant_ai_configs.api_key_enc nullable

Revision ID: 0007_nullable_apikey
Revises: 0006_notification_settings
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_nullable_apikey"
down_revision: Union[str, None] = "0006_notification_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "tenant_ai_configs",
        "api_key_enc",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "tenant_ai_configs",
        "api_key_enc",
        existing_type=sa.Text(),
        nullable=False,
    )
