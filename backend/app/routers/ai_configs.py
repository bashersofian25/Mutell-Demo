from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.crypto import encrypt_api_key
from app.core.deps import get_current_user
from app.models.ai_provider import AIProvider
from app.models.tenant_ai_config import TenantAIConfig
from app.models.user import User
from app.schemas.ai_config import AIConfigCreate, AIConfigListResponse, AIConfigResponse, AIConfigUpdate

router = APIRouter()


@router.get("/providers")
async def list_active_providers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(AIProvider)
        .where(AIProvider.is_active.is_(True))
        .order_by(AIProvider.display_name)
    )
    providers = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "slug": p.slug,
            "display_name": p.display_name,
            "supported_models": p.supported_models or [],
        }
        for p in providers
    ]


@router.get("", response_model=AIConfigListResponse)
async def list_ai_configs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can configure AI")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    query = (
        select(TenantAIConfig, AIProvider.slug, AIProvider.display_name)
        .outerjoin(AIProvider, TenantAIConfig.provider_id == AIProvider.id)
        .where(TenantAIConfig.tenant_id == user.tenant_id)
        .order_by(TenantAIConfig.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    items = []
    for config, provider_slug, provider_name in rows:
        items.append(AIConfigResponse(
            id=str(config.id),
            provider_id=str(config.provider_id),
            provider_slug=provider_slug,
            provider_name=provider_name,
            model_id=config.model_id,
            is_default=config.is_default,
            custom_prompt=config.custom_prompt,
            created_at=config.created_at.isoformat() if config.created_at else None,
        ))

    return AIConfigListResponse(items=items, total=len(items))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AIConfigResponse)
async def create_ai_config(
    body: AIConfigCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can configure AI")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    provider_result = await db.execute(select(AIProvider).where(AIProvider.id == UUID(body.provider_id)))
    provider = provider_result.scalar_one_or_none()
    if provider is None or not provider.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider not found or inactive")

    if body.is_default:
        existing = await db.execute(
            select(TenantAIConfig).where(
                TenantAIConfig.tenant_id == user.tenant_id,
                TenantAIConfig.is_default.is_(True),
            )
        )
        for old_config in existing.scalars().all():
            old_config.is_default = False
        await db.flush()

    config = TenantAIConfig(
        tenant_id=user.tenant_id,
        provider_id=UUID(body.provider_id),
        model_id=body.model_id,
        api_key_enc=encrypt_api_key(body.api_key) if body.api_key else None,
        is_default=body.is_default,
        custom_prompt=body.custom_prompt,
    )
    db.add(config)
    await db.flush()

    return AIConfigResponse(
        id=str(config.id),
        provider_id=str(config.provider_id),
        provider_slug=provider.slug,
        provider_name=provider.display_name,
        model_id=config.model_id,
        is_default=config.is_default,
        custom_prompt=config.custom_prompt,
        created_at=config.created_at.isoformat() if config.created_at else None,
    )


@router.patch("/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: UUID,
    body: AIConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can configure AI")

    result = await db.execute(select(TenantAIConfig).where(TenantAIConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None or (user.tenant_id and config.tenant_id != user.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI config not found")

    updates = body.model_dump(exclude_unset=True)
    if "api_key" in updates:
        raw = updates.pop("api_key")
        config.api_key_enc = encrypt_api_key(raw) if raw else None
    if "is_default" in updates and updates["is_default"]:
        existing = await db.execute(
            select(TenantAIConfig).where(
                TenantAIConfig.tenant_id == config.tenant_id,
                TenantAIConfig.is_default.is_(True),
            )
        )
        for old_config in existing.scalars().all():
            old_config.is_default = False
        await db.flush()

    for field, value in updates.items():
        setattr(config, field, value)
    await db.flush()

    provider_result = await db.execute(select(AIProvider).where(AIProvider.id == config.provider_id))
    provider = provider_result.scalar_one_or_none()

    return AIConfigResponse(
        id=str(config.id),
        provider_id=str(config.provider_id),
        provider_slug=provider.slug if provider else None,
        provider_name=provider.display_name if provider else None,
        model_id=config.model_id,
        is_default=config.is_default,
        custom_prompt=config.custom_prompt,
        created_at=config.created_at.isoformat() if config.created_at else None,
    )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    config_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can configure AI")

    result = await db.execute(select(TenantAIConfig).where(TenantAIConfig.id == config_id))
    config = result.scalar_one_or_none()
    if config is None or (user.tenant_id and config.tenant_id != user.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI config not found")

    await db.delete(config)
    await db.flush()
