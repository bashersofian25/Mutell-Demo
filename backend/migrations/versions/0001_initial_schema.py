"""Initial schema with all tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_terminals", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_slots_per_day", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("allowed_ai_providers", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("custom_prompt_allowed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("report_export_allowed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("api_rate_limit_per_min", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ai_providers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("supported_models", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="UTC"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("plan_id", sa.UUID(), sa.ForeignKey("plans.id"), nullable=True),
        sa.Column("slot_duration_secs", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("invite_token", sa.String(255), nullable=True),
        sa.Column("invite_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "user_permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "terminals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("api_key_hash", sa.String(255), nullable=False),
        sa.Column("api_key_prefix", sa.String(12), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "slots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("terminal_id", sa.UUID(), sa.ForeignKey("terminals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_secs", sa.Integer(), sa.Computed("EXTRACT(EPOCH FROM (ended_at - started_at))::INTEGER"), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_slots_tenant_started", "slots", ["tenant_id", "started_at"])
    op.create_index("idx_slots_terminal", "slots", ["terminal_id"])
    op.create_index("idx_slots_status", "slots", ["status"])

    op.create_table(
        "evaluations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slot_id", sa.UUID(), sa.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_provider", sa.String(50), nullable=False),
        sa.Column("ai_model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("score_overall", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_sentiment", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_politeness", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_compliance", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_resolution", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_upselling", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_response_time", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_honesty", sa.Numeric(5, 2), nullable=True),
        sa.Column("sentiment_label", sa.String(30), nullable=True),
        sa.Column("language_detected", sa.String(20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("strengths", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("weaknesses", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("recommendations", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("unclear_items", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("flags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("evaluation_duration_ms", sa.Integer(), nullable=True),
        sa.Column("is_unclear", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_evaluations_tenant", "evaluations", ["tenant_id"])
    op.create_index("idx_evaluations_slot", "evaluations", ["slot_id"])
    op.create_index("idx_evaluations_created", "evaluations", ["created_at"])

    op.create_table(
        "aggregated_evaluations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("terminal_id", sa.UUID(), sa.ForeignKey("terminals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("slot_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_overall", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_sentiment", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_politeness", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_compliance", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_resolution", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_upselling", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_response_time", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_honesty", sa.Numeric(5, 2), nullable=True),
        sa.Column("unclear_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flag_counts", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_agg_tenant_period",
        "aggregated_evaluations",
        ["tenant_id", "period_type", "period_start"],
        unique=True,
    )

    op.create_table(
        "notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slot_id", sa.UUID(), sa.ForeignKey("slots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tenant_ai_configs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.UUID(), sa.ForeignKey("ai_providers.id"), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("api_key_enc", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("custom_prompt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_by", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminal_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="generating"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("tenant_ai_configs")
    op.drop_table("notes")
    op.drop_table("aggregated_evaluations")
    op.drop_table("evaluations")
    op.drop_table("slots")
    op.drop_table("terminals")
    op.drop_table("user_permissions")
    op.drop_table("users")
    op.drop_table("tenants")
    op.drop_table("ai_providers")
    op.drop_table("plans")
