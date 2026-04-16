from datetime import datetime

from pydantic import BaseModel


class TerminalCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None


class TerminalUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None


class TerminalResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    api_key_prefix: str
    location: str | None
    status: str
    last_seen_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerminalCreated(TerminalResponse):
    api_key: str


class TerminalListResponse(BaseModel):
    items: list[TerminalResponse]
    total: int
