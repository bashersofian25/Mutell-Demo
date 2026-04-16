from pydantic import BaseModel


class AIConfigCreate(BaseModel):
    provider_id: str
    model_id: str
    api_key: str | None = None
    is_default: bool = False
    custom_prompt: str | None = None


class AIConfigUpdate(BaseModel):
    model_id: str | None = None
    api_key: str | None = None
    is_default: bool | None = None
    custom_prompt: str | None = None


class AIConfigResponse(BaseModel):
    id: str
    provider_id: str
    provider_slug: str | None = None
    provider_name: str | None = None
    model_id: str
    is_default: bool
    custom_prompt: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class AIConfigListResponse(BaseModel):
    items: list[AIConfigResponse]
    total: int
