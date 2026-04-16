import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AggregatedEvaluation(Base):
    __tablename__ = "aggregated_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "period_type",
            "period_start",
            name="uq_agg_tenant_period",
        ),
        Index("idx_agg_tenant_period", "tenant_id", "period_type", "period_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    terminal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("terminals.id", ondelete="SET NULL"))
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    avg_overall: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_sentiment: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_politeness: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_compliance: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_resolution: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_upselling: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_response_time: Mapped[float | None] = mapped_column(Numeric(5, 2))
    avg_honesty: Mapped[float | None] = mapped_column(Numeric(5, 2))

    unclear_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flag_counts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
