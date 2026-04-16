from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class SlotCreate(BaseModel):
    started_at: datetime
    ended_at: datetime
    raw_text: str = Field(..., max_length=100_000)
    metadata: dict[str, str | int | float | bool] | None = None

    @model_validator(mode="after")
    def check_dates(self) -> SlotCreate:
        if self.started_at and self.ended_at:
            if self.ended_at <= self.started_at:
                raise ValueError("ended_at must be after started_at")
        return self


class SlotResponse(BaseModel):
    id: str
    terminal_id: str | None
    tenant_id: str
    started_at: datetime
    ended_at: datetime
    duration_secs: int | None
    language: str | None
    word_count: int | None
    status: str
    tags: list[str] = []
    metadata: dict
    created_at: datetime
    score_overall: float | None = None

    model_config = {"from_attributes": True}


class SlotListResponse(BaseModel):
    items: list[SlotResponse]
    total: int
    page: int
    per_page: int


class SlotAccepted(BaseModel):
    slot_id: str
    status: str = "accepted"
    config: dict


class SlotDetail(SlotResponse):
    raw_text: str
    evaluation: "EvaluationResponse | None" = None


class ReEvaluateResponse(BaseModel):
    slot_id: str
    status: str = "re-evaluating"


class BulkReEvaluateRequest(BaseModel):
    slot_ids: list[str]


class BulkReEvaluateResponse(BaseModel):
    queued: int
    slot_ids: list[str]
