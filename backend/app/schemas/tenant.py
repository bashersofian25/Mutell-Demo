from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    name: str
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$")
    contact_email: EmailStr
    contact_phone: str | None = None
    address: str | None = None
    timezone: str = "UTC"
    plan_id: str | None = None
    slot_duration_secs: int = 300
    max_concurrent_evaluations: int | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    address: str | None = None
    timezone: str | None = None
    slot_duration_secs: int | None = None
    status: str | None = None
    plan_id: str | None = None
    max_concurrent_evaluations: int | None = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: str | None
    contact_email: EmailStr
    contact_phone: str | None
    address: str | None
    timezone: str
    status: str
    plan_id: str | None
    slot_duration_secs: int
    max_concurrent_evaluations: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
