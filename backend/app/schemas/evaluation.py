from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvaluationResponse(BaseModel):
    id: UUID
    slot_id: UUID
    tenant_id: UUID
    ai_provider: str
    ai_model: str
    prompt_version: str | None

    score_overall: float | None
    score_sentiment: float | None
    score_politeness: float | None
    score_compliance: float | None
    score_resolution: float | None
    score_upselling: float | None
    score_response_time: float | None
    score_honesty: float | None

    sentiment_label: str | None
    language_detected: str | None
    summary: str | None
    strengths: list[str] | None
    weaknesses: list[str] | None
    recommendations: list[str] | None
    unclear_items: list[str] | None
    flags: list[str] | None

    unavailable_items: list[str] | None
    swearing_count: int | None
    swearing_instances: list[str] | None
    off_topic_count: int | None
    off_topic_segments: list[str] | None
    speaker_segments: list[dict] | None

    tokens_used: int | None
    evaluation_duration_ms: int | None
    is_unclear: bool

    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListResponse(BaseModel):
    items: list[EvaluationResponse]
    total: int
    page: int
    per_page: int
