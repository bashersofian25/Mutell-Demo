from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    slot_id: str
    content: str = Field(..., min_length=1)


class NoteUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str | None
    slot_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
