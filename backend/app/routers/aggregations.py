from typing import Literal

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.aggregation import AggregationListResponse
from app.services.aggregation_service import AggregationService

router = APIRouter()


@router.get("", response_model=AggregationListResponse)
async def list_aggregations(
    period_type: Literal["hour", "day", "week", "month"] = Query("day"),
    period_start: str | None = None,
    period_end: str | None = None,
    terminal_id: UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = AggregationService(db)
    try:
        return await svc.get_aggregations(
            tenant_id=str(user.tenant_id),
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            terminal_id=str(terminal_id) if terminal_id else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
