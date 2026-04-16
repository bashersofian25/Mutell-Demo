import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        Index("idx_evaluations_tenant", "tenant_id"),
        Index("idx_evaluations_slot", "slot_id"),
        Index("idx_evaluations_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("slots.id", ondelete="CASCADE"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    ai_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(50))

    score_overall: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_sentiment: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_politeness: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_compliance: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_resolution: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_upselling: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_response_time: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_honesty: Mapped[float | None] = mapped_column(Numeric(5, 2))

    sentiment_label: Mapped[str | None] = mapped_column(String(30))
    language_detected: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    weaknesses: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    recommendations: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    unclear_items: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    flags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    unavailable_items: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    swearing_count: Mapped[int | None] = mapped_column(Integer)
    swearing_instances: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    off_topic_segments: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    off_topic_count: Mapped[int | None] = mapped_column(Integer)
    speaker_segments: Mapped[dict | None] = mapped_column(JSONB)

    raw_response: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    evaluation_duration_ms: Mapped[int | None] = mapped_column(Integer)
    is_unclear: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
