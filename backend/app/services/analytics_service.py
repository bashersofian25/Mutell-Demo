from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.slot import Slot
from app.schemas.analytics import (
    AnalyticsSummary,
    ScoreBreakdown,
    TagStats,
    TrendPoint,
)

TAG_LABELS = {
    "items_unavailable": "Items Unavailable",
    "swearing": "Swearing",
    "off_topic": "Off-Topic",
    "low_politeness": "Low Politeness",
    "rude_behavior": "Rude Behavior",
    "policy_violation": "Policy Violation",
    "excellent_service": "Excellent Service",
    "upsell_opportunity": "Upsell Opportunity",
    "compliance_issue": "Compliance Issue",
    "long_silence": "Long Silence",
}


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(
        self,
        tenant_id: str,
        date_from: str | None = None,
        date_to: str | None = None,
        terminal_id: str | None = None,
    ) -> AnalyticsSummary:
        tid = UUID(tenant_id)

        base = select(Slot).where(Slot.tenant_id == tid)
        if terminal_id:
            base = base.where(Slot.terminal_id == UUID(terminal_id))
        if date_from:
            base = base.where(Slot.started_at >= datetime.fromisoformat(date_from))
        if date_to:
            base = base.where(Slot.started_at <= datetime.fromisoformat(date_to))

        slots_result = await self.db.execute(base)
        slots = slots_result.scalars().all()

        status_dist: dict[str, int] = {}
        for s in slots:
            status_dist[s.status] = status_dist.get(s.status, 0) + 1

        slot_ids = [s.id for s in slots]

        evals: list[Evaluation] = []
        if slot_ids:
            eval_result = await self.db.execute(
                select(Evaluation).where(Evaluation.slot_id.in_(slot_ids))
            )
            evals = eval_result.scalars().all()

        def _avg(field: str) -> float | None:
            vals = [float(getattr(e, field)) for e in evals if getattr(e, field) is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        tag_counts: dict[str, int] = {}
        for s in slots:
            for tag in (s.tags or []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        tag_stats = sorted(
            [TagStats(tag=t, count=c, label=TAG_LABELS.get(t, t.replace("_", " ").title())) for t, c in tag_counts.items()],
            key=lambda x: x.count,
            reverse=True,
        )

        total_swearing = sum(e.swearing_count or 0 for e in evals)
        total_off_topic = sum(e.off_topic_count or 0 for e in evals)

        unavailable_freq: dict[str, int] = {}
        for e in evals:
            for item in (e.unavailable_items or []):
                unavailable_freq[item] = unavailable_freq.get(item, 0) + 1
        unavailable_freq = dict(sorted(unavailable_freq.items(), key=lambda x: x[1], reverse=True))

        lang_dist: dict[str, int] = {}
        for e in evals:
            if e.language_detected:
                lang_dist[e.language_detected] = lang_dist.get(e.language_detected, 0) + 1

        durations = [e.evaluation_duration_ms for e in evals if e.evaluation_duration_ms is not None]
        avg_duration = round(sum(durations) / len(durations), 1) if durations else None

        tokens = [e.tokens_used for e in evals if e.tokens_used is not None]
        avg_tokens = round(sum(tokens) / len(tokens), 1) if tokens else None

        trend = await self._compute_trend(tid, date_from, date_to, terminal_id)

        return AnalyticsSummary(
            total_slots=len(slots),
            evaluated_slots=status_dist.get("evaluated", 0) + status_dist.get("unclear", 0),
            failed_slots=status_dist.get("failed", 0),
            pending_slots=status_dist.get("pending", 0) + status_dist.get("queued", 0) + status_dist.get("processing", 0),
            avg_scores=ScoreBreakdown(
                overall=_avg("score_overall"),
                sentiment=_avg("score_sentiment"),
                politeness=_avg("score_politeness"),
                compliance=_avg("score_compliance"),
                resolution=_avg("score_resolution"),
                upselling=_avg("score_upselling"),
                response_time=_avg("score_response_time"),
                honesty=_avg("score_honesty"),
            ),
            score_trend=trend,
            tag_stats=tag_stats,
            total_swearing_incidents=total_swearing,
            total_off_topic_incidents=total_off_topic,
            total_unavailable_items=sum(unavailable_freq.values()),
            unavailable_item_frequency=unavailable_freq,
            language_distribution=lang_dist,
            status_distribution=status_dist,
            avg_duration_ms=avg_duration,
            avg_tokens_used=avg_tokens,
            period_start=datetime.fromisoformat(date_from) if date_from else None,
            period_end=datetime.fromisoformat(date_to) if date_to else None,
        )

    async def _compute_trend(
        self,
        tenant_id: UUID,
        date_from: str | None,
        date_to: str | None,
        terminal_id: str | None,
    ) -> list[TrendPoint]:
        from app.models.aggregated_evaluation import AggregatedEvaluation

        query = select(AggregatedEvaluation).where(
            AggregatedEvaluation.tenant_id == tenant_id,
            AggregatedEvaluation.period_type == "day",
        )
        if date_from:
            query = query.where(AggregatedEvaluation.period_start >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.where(AggregatedEvaluation.period_start <= datetime.fromisoformat(date_to))
        if terminal_id:
            query = query.where(AggregatedEvaluation.terminal_id == UUID(terminal_id))

        query = query.order_by(AggregatedEvaluation.period_start.asc())
        result = await self.db.execute(query)
        aggs = result.scalars().all()

        return [
            TrendPoint(
                period=agg.period_start.strftime("%Y-%m-%d"),
                overall=float(agg.avg_overall) if agg.avg_overall is not None else None,
                sentiment=float(agg.avg_sentiment) if agg.avg_sentiment is not None else None,
                politeness=float(agg.avg_politeness) if agg.avg_politeness is not None else None,
                compliance=float(agg.avg_compliance) if agg.avg_compliance is not None else None,
            )
            for agg in aggs
        ]
