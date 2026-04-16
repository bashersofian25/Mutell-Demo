from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.ai_provider import AIProvider
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanListResponse, PlanResponse, PlanUpdate
from app.schemas.tenant import TenantCreate, TenantListResponse, TenantResponse, TenantUpdate
from app.schemas.user import UserListResponse, UserUpdate
from pydantic import BaseModel


class AIProviderUpdateRequest(BaseModel):
    is_active: bool | None = None
    display_name: str | None = None
    api_key: str | None = None


class AIProviderModelRequest(BaseModel):
    model_id: str


from app.routers.plans import _to_response as _plan_to_response
from app.routers.tenants import _to_response as _tenant_to_response

router = APIRouter()

require_super_admin = require_role("super_admin")


@router.get("/tenants", response_model=TenantListResponse)
async def admin_list_tenants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Tenant)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Tenant.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    tenants = result.scalars().all()

    return TenantListResponse(items=[_tenant_to_response(t) for t in tenants], total=total)


@router.post("/tenants", status_code=status.HTTP_201_CREATED, response_model=TenantResponse)
async def admin_create_tenant(
    body: TenantCreate,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
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

    return _tenant_to_response(tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def admin_get_tenant(
    tenant_id: UUID,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return _tenant_to_response(tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
async def admin_update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.routers.tenants import _apply_tenant_update

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    _apply_tenant_update(tenant, body.model_dump(exclude_unset=True))
    await db.flush()

    return _tenant_to_response(tenant)


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_tenant(
    tenant_id: UUID,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    tenant.status = "deleted"

    from app.models.terminal import Terminal
    terminal_result = await db.execute(
        select(Terminal).where(Terminal.tenant_id == tenant_id, Terminal.status == "active")
    )
    for t in terminal_result.scalars().all():
        t.status = "revoked"

    await db.flush()


@router.get("/plans", response_model=PlanListResponse)
async def admin_list_plans(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Plan)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Plan.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    plans = result.scalars().all()

    return PlanListResponse(items=[_plan_to_response(p) for p in plans], total=total)


@router.post("/plans", status_code=status.HTTP_201_CREATED, response_model=PlanResponse)
async def admin_create_plan(
    body: PlanCreate,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    return _plan_to_response(plan)


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def admin_update_plan(
    plan_id: UUID,
    body: PlanUpdate,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.flush()

    return _plan_to_response(plan)


@router.get("/ai-providers")
async def admin_list_ai_providers(
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).order_by(AIProvider.display_name))
    providers = result.scalars().all()
    data_list = []
    for p in providers:
        masked = None
        if p.api_key_enc:
            try:
                from app.core.crypto import decrypt_api_key
                raw = decrypt_api_key(p.api_key_enc)
                masked = (raw[:4] + "..." + raw[-4:]) if len(raw) > 8 else "****"
            except Exception:
                masked = "****"
        data_list.append({
            "id": str(p.id),
            "slug": p.slug,
            "display_name": p.display_name,
            "is_active": p.is_active,
            "api_key": masked,
            "supported_models": p.supported_models,
        })
    return {"success": True, "data": data_list}


@router.patch("/ai-providers/{provider_id}")
async def admin_update_ai_provider(
    provider_id: UUID,
    body: AIProviderUpdateRequest,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    if body.is_active is not None:
        provider.is_active = body.is_active
    if body.display_name is not None:
        provider.display_name = body.display_name
    if body.api_key is not None:
        from app.core.crypto import encrypt_api_key
        provider.api_key_enc = encrypt_api_key(body.api_key)
    await db.flush()

    masked_key = None
    if provider.api_key_enc:
        try:
            from app.core.crypto import decrypt_api_key
            raw = decrypt_api_key(provider.api_key_enc)
            masked_key = (raw[:4] + "..." + raw[-4:]) if len(raw) > 8 else "****"
        except Exception:
            masked_key = "****"

    return {
        "success": True,
        "data": {
            "id": str(provider.id),
            "slug": provider.slug,
            "display_name": provider.display_name,
            "is_active": provider.is_active,
            "api_key": masked_key,
            "supported_models": provider.supported_models,
        },
    }


@router.post("/ai-providers/{provider_id}/models")
async def admin_add_provider_model(
    provider_id: UUID,
    body: AIProviderModelRequest,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    models = provider.supported_models or []
    if body.model_id not in models:
        models.append(body.model_id)
        provider.supported_models = models
        await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(provider.id),
            "slug": provider.slug,
            "display_name": provider.display_name,
            "supported_models": provider.supported_models,
        },
    }


@router.delete("/ai-providers/{provider_id}/models/{model_id:path}")
async def admin_remove_provider_model(
    provider_id: UUID,
    model_id: str,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    models = provider.supported_models or []
    if model_id in models:
        models.remove(model_id)
        provider.supported_models = models
        await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(provider.id),
            "slug": provider.slug,
            "display_name": provider.display_name,
            "supported_models": provider.supported_models,
        },
    }


@router.get("/users", response_model=UserListResponse)
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.routers.users import _to_response as _user_to_response
    query = select(User)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(items=[_user_to_response(u) for u in users], total=total)


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.routers.users import _to_response as _user_to_response

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await db.flush()

    return _user_to_response(target)


@router.get("/audit-log")
async def admin_audit_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.audit_log import AuditLog
    from datetime import datetime

    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if date_from:
        try:
            query = query.where(AuditLog.created_at >= datetime.fromisoformat(date_from))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_from: {date_from}")
    if date_to:
        try:
            query = query.where(AuditLog.created_at <= datetime.fromisoformat(date_to))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_to: {date_to}")

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(l.id),
                "tenant_id": str(l.tenant_id) if l.tenant_id else None,
                "user_id": str(l.user_id) if l.user_id else None,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "detail": l.detail,
                "ip_address": l.ip_address,
                "status_code": l.status_code,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/health")
async def admin_health(
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    import asyncio
    from app.core.config import settings

    health_data = {
        "database": "connected",
        "redis": "unknown",
        "workers": "unknown",
    }

    try:
        import redis as redis_lib

        def _ping_redis():
            r = redis_lib.from_url(settings.REDIS_URL)
            r.ping()
            r.close()

        await asyncio.get_running_loop().run_in_executor(None, _ping_redis)
        health_data["redis"] = "connected"
    except Exception:
        health_data["redis"] = "disconnected"

    return {"success": True, "data": health_data}
