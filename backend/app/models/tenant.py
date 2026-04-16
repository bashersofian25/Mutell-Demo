import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    plan_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("plans.id"))
    slot_duration_secs: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    max_concurrent_evaluations: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    plan = relationship("Plan", lazy="selectin")
    terminals = relationship("Terminal", back_populates="tenant", lazy="selectin")
    users = relationship("User", back_populates="tenant", lazy="selectin")
