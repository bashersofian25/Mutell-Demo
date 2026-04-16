from datetime import datetime

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    max_terminals: int = Field(ge=1, default=5)
    max_users: int = Field(ge=1, default=10)
    max_slots_per_day: int = Field(ge=1, default=1000)
    retention_days: int = Field(ge=1, default=90)
    allowed_ai_providers: list[str] = []
    custom_prompt_allowed: bool = False
    report_export_allowed: bool = True
    api_rate_limit_per_min: int = Field(ge=1, default=60)
    max_concurrent_evaluations: int = Field(ge=1, default=2)


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    max_terminals: int | None = Field(default=None, ge=1)
    max_users: int | None = Field(default=None, ge=1)
    max_slots_per_day: int | None = Field(default=None, ge=1)
    retention_days: int | None = Field(default=None, ge=1)
    allowed_ai_providers: list[str] | None = None
    custom_prompt_allowed: bool | None = None
    report_export_allowed: bool | None = None
    api_rate_limit_per_min: int | None = Field(default=None, ge=1)
    max_concurrent_evaluations: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class PlanResponse(BaseModel):
    id: str
    name: str
    description: str | None
    max_terminals: int
    max_users: int
    max_slots_per_day: int
    retention_days: int
    allowed_ai_providers: list[str]
    custom_prompt_allowed: bool
    report_export_allowed: bool
    api_rate_limit_per_min: int
    max_concurrent_evaluations: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    items: list[PlanResponse]
    total: int
