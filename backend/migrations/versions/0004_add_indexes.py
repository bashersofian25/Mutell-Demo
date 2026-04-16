"""Add missing indexes and extend aggregation unique constraint

Revision ID: 0004_add_indexes
Revises: 0003_user_reset_tokens
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_add_indexes"
down_revision: Union[str, None] = "0003_user_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_notes_tenant_slot", "notes", ["tenant_id", "slot_id"])

    op.create_index("idx_tenant_ai_configs_tenant_default", "tenant_ai_configs", ["tenant_id", "is_default"])

    op.create_index("idx_reports_tenant_status", "reports", ["tenant_id", "status"])

    op.create_index("idx_terminals_tenant", "terminals", ["tenant_id"])

    op.create_index("idx_user_permissions_user_perm", "user_permissions", ["user_id", "permission"], unique=True)

    op.create_index("idx_tenants_status", "tenants", ["status"])

    op.create_index("idx_users_reset_token", "users", ["reset_token"])
    op.create_index("idx_users_invite_token", "users", ["invite_token"])


def downgrade() -> None:
    op.drop_index("idx_users_invite_token", table_name="users")
    op.drop_index("idx_users_reset_token", table_name="users")

    op.drop_index("idx_tenants_status", table_name="tenants")

    op.drop_index("idx_user_permissions_user_perm", table_name="user_permissions")

    op.drop_index("idx_terminals_tenant", table_name="terminals")

    op.drop_index("idx_reports_tenant_status", table_name="reports")

    op.drop_index("idx_tenant_ai_configs_tenant_default", table_name="tenant_ai_configs")

    op.drop_index("idx_notes_tenant_slot", table_name="notes")
