from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import generate_api_key
from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.terminal import Terminal
from app.models.user import User
from app.schemas.terminal import (
    TerminalCreate,
    TerminalCreated,
    TerminalListResponse,
    TerminalResponse,
    TerminalUpdate,
)

router = APIRouter()


def _to_response(t: Terminal) -> TerminalResponse:
    return TerminalResponse(
        id=str(t.id),
        tenant_id=str(t.tenant_id),
        name=t.name,
        description=t.description,
        api_key_prefix=t.api_key_prefix,
        location=t.location,
        status=t.status,
        last_seen_at=t.last_seen_at,
        created_at=t.created_at,
    )


@router.get("", response_model=TerminalListResponse)
async def list_terminals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    query = select(Terminal)
    if user.tenant_id:
        query = query.where(Terminal.tenant_id == user.tenant_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Terminal.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    terminals = result.scalars().all()

    return TerminalListResponse(
        items=[_to_response(t) for t in terminals],
        total=total,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TerminalCreated)
async def create_terminal(
    body: TerminalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    count_result = await db.execute(
        select(func.count()).select_from(Terminal).where(Terminal.tenant_id == user.tenant_id)
    )
    terminal_count = count_result.scalar() or 0

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if tenant and tenant.plan_id:
        plan_result = await db.execute(select(Plan).where(Plan.id == tenant.plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan and terminal_count >= plan.max_terminals:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Terminal limit reached",
            )

    raw_key, prefix, key_hash = generate_api_key()

    terminal = Terminal(
        tenant_id=user.tenant_id,
        name=body.name,
        description=body.description,
        api_key_hash=key_hash,
        api_key_prefix=prefix,
        location=body.location,
    )
    db.add(terminal)
    await db.flush()

    resp = TerminalCreated(
        id=str(terminal.id),
        tenant_id=str(terminal.tenant_id),
        name=terminal.name,
        description=terminal.description,
        api_key_prefix=terminal.api_key_prefix,
        location=terminal.location,
        status=terminal.status,
        last_seen_at=terminal.last_seen_at,
        created_at=terminal.created_at,
        api_key=f"pk_live_{raw_key}",
    )
    return resp


@router.patch("/{terminal_id}", response_model=TerminalResponse)
async def update_terminal(
    terminal_id: UUID,
    body: TerminalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = await db.execute(
        select(Terminal).where(Terminal.id == terminal_id, Terminal.tenant_id == user.tenant_id)
    )
    terminal = result.scalar_one_or_none()
    if terminal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal not found")

    if body.name is not None:
        terminal.name = body.name
    if body.description is not None:
        terminal.description = body.description
    if body.location is not None:
        terminal.location = body.location
    await db.flush()

    return _to_response(terminal)


@router.delete("/{terminal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_terminal(
    terminal_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = await db.execute(
        select(Terminal).where(Terminal.id == terminal_id, Terminal.tenant_id == user.tenant_id)
    )
    terminal = result.scalar_one_or_none()
    if terminal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal not found")

    terminal.status = "revoked"
    await db.flush()


@router.post("/{terminal_id}/ping")
async def ping_terminal(
    terminal_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = await db.execute(
        select(Terminal).where(Terminal.id == terminal_id, Terminal.tenant_id == user.tenant_id)
    )
    terminal = result.scalar_one_or_none()
    if terminal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal not found")

    terminal.last_seen_at = datetime.now(UTC)
    await db.flush()

    return {"success": True, "data": {"terminal_id": str(terminal.id), "last_seen_at": terminal.last_seen_at.isoformat() if terminal.last_seen_at else None}}


@router.post("/{terminal_id}/regenerate-key", response_model=TerminalCreated)
async def regenerate_key(
    terminal_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    result = await db.execute(
        select(Terminal).where(Terminal.id == terminal_id, Terminal.tenant_id == user.tenant_id)
    )
    terminal = result.scalar_one_or_none()
    if terminal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal not found")

    raw_key, prefix, key_hash = generate_api_key()
    terminal.api_key_hash = key_hash
    terminal.api_key_prefix = prefix
    await db.flush()

    resp = TerminalCreated(
        id=str(terminal.id),
        tenant_id=str(terminal.tenant_id),
        name=terminal.name,
        description=terminal.description,
        api_key_prefix=terminal.api_key_prefix,
        api_key=f"pk_live_{raw_key}",
        location=terminal.location,
        status=terminal.status,
        last_seen_at=terminal.last_seen_at,
        created_at=terminal.created_at,
    )
    return resp
