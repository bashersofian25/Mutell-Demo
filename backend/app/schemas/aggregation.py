from datetime import datetime

from pydantic import BaseModel


class AggregationResponse(BaseModel):
    id: str | None
    tenant_id: str
    terminal_id: str | None
    period_type: str
    period_start: datetime
    period_end: datetime
    slot_count: int

    avg_overall: float | None
    avg_sentiment: float | None
    avg_politeness: float | None
    avg_compliance: float | None
    avg_resolution: float | None
    avg_upselling: float | None
    avg_response_time: float | None
    avg_honesty: float | None

    unclear_count: int
    flag_counts: dict

    computed_at: datetime

    model_config = {"from_attributes": True}


class AggregationListResponse(BaseModel):
    items: list[AggregationResponse]
    total: int
