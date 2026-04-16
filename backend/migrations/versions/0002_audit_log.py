"""Add audit_logs table

Revision ID: 0002_audit_log
Revises: 0001_initial
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_audit_log"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_tenant_created", "audit_logs", ["tenant_id", "created_at"])
    op.create_index("idx_audit_action", "audit_logs", ["action"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_user")
    op.drop_index("idx_audit_action")
    op.drop_index("idx_audit_tenant_created")
    op.drop_table("audit_logs")
