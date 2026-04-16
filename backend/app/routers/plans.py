from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.plan import Plan
from app.models.user import User
from app.schemas.plan import (
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
)

router = APIRouter()


def _to_response(p: Plan) -> PlanResponse:
    return PlanResponse(
        id=str(p.id),
        name=p.name,
        description=p.description,
        max_terminals=p.max_terminals,
        max_users=p.max_users,
        max_slots_per_day=p.max_slots_per_day,
        retention_days=p.retention_days,
        allowed_ai_providers=p.allowed_ai_providers or [],
        custom_prompt_allowed=p.custom_prompt_allowed,
        report_export_allowed=p.report_export_allowed,
        api_rate_limit_per_min=p.api_rate_limit_per_min,
        max_concurrent_evaluations=p.max_concurrent_evaluations,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=PlanListResponse)
async def list_plans(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan)
    if user.role != "super_admin":
        query = query.where(Plan.is_active.is_(True))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Plan.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    plans = result.scalars().all()

    return PlanListResponse(items=[_to_response(p) for p in plans], total=total)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlanResponse)
async def create_plan(
    body: PlanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin only")

    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()

    return _to_response(plan)


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan).where(Plan.id == plan_id)
    if user.role != "super_admin":
        query = query.where(Plan.is_active.is_(True))
    result = await db.execute(query)
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _to_response(plan)


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: UUID,
    body: PlanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin only")

    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()

    return _to_response(plan)
