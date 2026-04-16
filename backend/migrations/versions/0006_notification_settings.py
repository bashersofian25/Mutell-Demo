"""Add notification_settings table

Revision ID: 0006_notification_settings
Revises: 0005_provider_api_key
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_notification_settings"
down_revision: Union[str, None] = "0005_provider_api_key"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("email_evaluations", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_failures", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_reports", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("push_mentions", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("push_weekly_summary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
