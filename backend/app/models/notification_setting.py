import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    email_evaluations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_failures: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_reports: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_mentions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_weekly_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="notification_settings")
