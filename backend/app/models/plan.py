import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    max_terminals: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_slots_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    allowed_ai_providers: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    custom_prompt_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    report_export_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_rate_limit_per_min: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_concurrent_evaluations: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
