from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TagStats(BaseModel):
    tag: str
    count: int
    label: str


class ScoreBreakdown(BaseModel):
    overall: float | None
    sentiment: float | None
    politeness: float | None
    compliance: float | None
    resolution: float | None
    upselling: float | None
    response_time: float | None
    honesty: float | None


class TrendPoint(BaseModel):
    period: str
    overall: float | None
    sentiment: float | None
    politeness: float | None
    compliance: float | None


class AnalyticsSummary(BaseModel):
    total_slots: int
    evaluated_slots: int
    failed_slots: int
    pending_slots: int

    avg_scores: ScoreBreakdown
    score_trend: list[TrendPoint]

    tag_stats: list[TagStats]
    total_swearing_incidents: int
    total_off_topic_incidents: int
    total_unavailable_items: int
    unavailable_item_frequency: dict[str, int]

    language_distribution: dict[str, int]
    status_distribution: dict[str, int]

    avg_duration_ms: float | None
    avg_tokens_used: float | None

    period_start: datetime | None
    period_end: datetime | None
