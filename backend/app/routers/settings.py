from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notification_setting import NotificationSetting
from app.models.user import User
from app.schemas.notification import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)

router = APIRouter()


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = NotificationSetting(user_id=user.id)
        db.add(settings)
        await db.flush()
    return NotificationSettingsResponse.model_validate(settings)


@router.put("/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = NotificationSetting(user_id=user.id, **body.model_dump())
        db.add(settings)
    else:
        settings.email_evaluations = body.email_evaluations
        settings.email_failures = body.email_failures
        settings.email_reports = body.email_reports
        settings.push_mentions = body.push_mentions
        settings.push_weekly_summary = body.push_weekly_summary
    await db.flush()
    return NotificationSettingsResponse.model_validate(settings)
