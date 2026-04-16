from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    terminal_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = AnalyticsService(db)
    return await svc.get_summary(
        tenant_id=str(user.tenant_id),
        date_from=date_from,
        date_to=date_to,
        terminal_id=terminal_id,
    )
