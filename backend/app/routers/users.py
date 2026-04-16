import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.user import User, UserPermission
from app.schemas.user import (
    PERMISSIONS_SCHEMA,
    ROLE_HIERARCHY,
    PermissionListResponse,
    PermissionUpdate,
    UserInvite,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


def _to_response(u: User) -> UserResponse:
    return UserResponse(
        id=str(u.id),
        tenant_id=str(u.tenant_id) if u.tenant_id else None,
        email=u.email,
        full_name=u.full_name,
        avatar_url=u.avatar_url,
        role=u.role,
        status=u.status,
        last_login_at=u.last_login_at,
        created_at=u.created_at,
        max_concurrent_evaluations=u.max_concurrent_evaluations if u.max_concurrent_evaluations is not None else 1,
    )


@router.get("/meta/permissions")
async def list_permission_schema(
    user: User = Depends(get_current_user),
):
    return {"permissions": PERMISSIONS_SCHEMA}


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role_filter: str | None = Query(None, alias="role"),
    status_filter: str | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    query = select(User)
    if user.tenant_id:
        query = query.where(User.tenant_id == user.tenant_id)
    if search:
        query = query.where(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
    if role_filter:
        query = query.where(User.role == role_filter)
    if status_filter:
        query = query.where(User.status == status_filter)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(items=[_to_response(u) for u in users], total=total)


@router.post("/invite", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def invite_user(
    body: UserInvite,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    if ROLE_HIERARCHY.get(body.role, 0) > ROLE_HIERARCHY.get(user.role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot invite user with role '{body.role}' above your own role",
        )

    count_result = await db.execute(
        select(func.count()).select_from(User).where(User.tenant_id == user.tenant_id)
    )
    user_count = count_result.scalar() or 0

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if tenant and tenant.plan_id:
        plan_result = await db.execute(select(Plan).where(Plan.id == tenant.plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan and user_count >= plan.max_users:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="User limit reached",
            )

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    new_user = User(
        tenant_id=user.tenant_id,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        status="invited",
        invite_token=token_hash,
        invite_expires=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(new_user)
    await db.flush()

    from app.services.notification_service import NotificationService
    notif_svc = NotificationService(db)
    await notif_svc.send_user_invited(body.email, token)

    return _to_response(new_user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_self = str(user_id) == str(current_user.id)
    if not is_self and current_user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role != "super_admin" and target.tenant_id != current_user.tenant_id and not is_self:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied")

    if not is_self and body.role is not None:
        if ROLE_HIERARCHY.get(body.role, 0) > ROLE_HIERARCHY.get(current_user.role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot assign role '{body.role}' above your own level",
            )

    if is_self:
        if body.full_name is not None:
            target.full_name = body.full_name
    else:
        if body.full_name is not None:
            target.full_name = body.full_name
        if body.role is not None:
            target.role = body.role
        if body.status is not None:
            target.status = body.status
        if body.max_concurrent_evaluations is not None:
            target.max_concurrent_evaluations = body.max_concurrent_evaluations
    await db.flush()

    return _to_response(target)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role != "super_admin" and target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied")

    target.status = "suspended"
    await db.flush()


@router.put("/{user_id}/permissions")
async def update_permissions(
    user_id: UUID,
    body: list[PermissionUpdate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    query = select(User).where(User.id == user_id)
    if current_user.role != "super_admin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")
        query = query.where(User.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing_result = await db.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
    )
    existing = {p.permission: p for p in existing_result.scalars().all()}

    for perm in body:
        if perm.permission in existing:
            existing[perm.permission].granted = perm.granted
        else:
            db.add(UserPermission(
                user_id=user_id,
                permission=perm.permission,
                granted=perm.granted,
            ))
    await db.flush()

    return {"success": True}


@router.get("/{user_id}/permissions", response_model=PermissionListResponse)
async def get_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    query = select(User).where(User.id == user_id)
    if current_user.role != "super_admin":
        if not current_user.tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")
        query = query.where(User.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    perm_result = await db.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
    )
    perms = perm_result.scalars().all()

    return PermissionListResponse(
        user_id=str(user_id),
        permissions=[{"permission": p.permission, "granted": p.granted} for p in perms],
    )
