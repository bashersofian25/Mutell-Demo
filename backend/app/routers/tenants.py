from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)

router = APIRouter()


def _to_response(t: Tenant) -> TenantResponse:
    return TenantResponse(
        id=str(t.id),
        name=t.name,
        slug=t.slug,
        logo_url=t.logo_url,
        contact_email=t.contact_email,
        contact_phone=t.contact_phone,
        address=t.address,
        timezone=t.timezone,
        status=t.status,
        plan_id=str(t.plan_id) if t.plan_id else None,
        slot_duration_secs=t.slot_duration_secs,
        max_concurrent_evaluations=t.max_concurrent_evaluations,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin":
        if user.tenant_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one_or_none()
        tenants = [tenant] if tenant else []
        return TenantListResponse(items=[_to_response(t) for t in tenants], total=len(tenants))

    query = select(Tenant)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Tenant.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    tenants = result.scalars().all()

    return TenantListResponse(items=[_to_response(t) for t in tenants], total=total)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TenantResponse)
async def create_tenant(
    body: TenantCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin only")

    existing = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken")

    tenant = Tenant(
        name=body.name,
        slug=body.slug,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
        address=body.address,
        timezone=body.timezone,
        plan_id=UUID(body.plan_id) if body.plan_id else None,
        slot_duration_secs=body.slot_duration_secs,
        max_concurrent_evaluations=body.max_concurrent_evaluations,
    )
    db.add(tenant)
    await db.flush()

    return _to_response(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin" and str(user.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return _to_response(tenant)


TENANT_UPDATE_ALLOWED_FIELDS = {"name", "contact_email", "contact_phone", "address", "timezone", "slot_duration_secs", "plan_id", "max_concurrent_evaluations"}


def _apply_tenant_update(tenant: Tenant, data: dict) -> None:
    for field, value in data.items():
        if field not in TENANT_UPDATE_ALLOWED_FIELDS:
            continue
        if field == "plan_id" and value is not None:
            value = UUID(value)
        setattr(tenant, field, value)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin" and (user.role != "tenant_admin" or str(user.tenant_id) != str(tenant_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    _apply_tenant_update(tenant, body.model_dump(exclude_unset=True))
    await db.flush()

    return _to_response(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin only")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    tenant.status = "deleted"
    await db.flush()
