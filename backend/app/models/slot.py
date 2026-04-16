import uuid
from datetime import UTC, datetime

from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        Index("idx_slots_tenant_started", "tenant_id", "started_at"),
        Index("idx_slots_terminal", "terminal_id"),
        Index("idx_slots_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    terminal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("terminals.id", ondelete="SET NULL"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_secs: Mapped[int | None] = mapped_column(
        Integer,
        Computed("EXTRACT(EPOCH FROM (ended_at - started_at))::INTEGER", persisted=True),
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20))
    word_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
