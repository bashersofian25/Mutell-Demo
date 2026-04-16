from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregated_evaluation import AggregatedEvaluation
from app.models.evaluation import Evaluation
from app.schemas.aggregation import AggregationListResponse, AggregationResponse


class AggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_aggregations(
        self,
        tenant_id: str,
        period_type: str,
        period_start: str | None,
        period_end: str | None,
        terminal_id: str | None = None,
    ) -> AggregationListResponse:
        query = select(AggregatedEvaluation).where(
            AggregatedEvaluation.tenant_id == UUID(tenant_id),
            AggregatedEvaluation.period_type == period_type,
        )

        if terminal_id:
            query = query.where(AggregatedEvaluation.terminal_id == UUID(terminal_id))
        if period_start:
            try:
                query = query.where(AggregatedEvaluation.period_start >= datetime.fromisoformat(period_start))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid period_start format: {period_start}")
        if period_end:
            try:
                query = query.where(AggregatedEvaluation.period_end <= datetime.fromisoformat(period_end))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid period_end format: {period_end}")

        query = query.order_by(AggregatedEvaluation.period_start.desc())
        result = await self.db.execute(query)
        aggregations = result.scalars().all()

        return AggregationListResponse(
            items=[
                AggregationResponse(
                    id=str(a.id),
                    tenant_id=str(a.tenant_id),
                    terminal_id=str(a.terminal_id) if a.terminal_id else None,
                    period_type=a.period_type,
                    period_start=a.period_start,
                    period_end=a.period_end,
                    slot_count=a.slot_count,
                    avg_overall=float(a.avg_overall) if a.avg_overall is not None else None,
                    avg_sentiment=float(a.avg_sentiment) if a.avg_sentiment is not None else None,
                    avg_politeness=float(a.avg_politeness) if a.avg_politeness is not None else None,
                    avg_compliance=float(a.avg_compliance) if a.avg_compliance is not None else None,
                    avg_resolution=float(a.avg_resolution) if a.avg_resolution is not None else None,
                    avg_upselling=float(a.avg_upselling) if a.avg_upselling is not None else None,
                    avg_response_time=float(a.avg_response_time) if a.avg_response_time is not None else None,
                    avg_honesty=float(a.avg_honesty) if a.avg_honesty is not None else None,
                    unclear_count=a.unclear_count,
                    flag_counts=a.flag_counts,
                    computed_at=a.computed_at,
                )
                for a in aggregations
            ],
            total=len(aggregations),
        )

    async def compute_aggregation(
        self,
        tenant_id: str,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        terminal_id: str | None = None,
    ) -> AggregationResponse:
        tid = UUID(tenant_id)
        query = select(Evaluation).where(
            Evaluation.tenant_id == tid,
            Evaluation.created_at >= period_start,
            Evaluation.created_at < period_end,
        )

        evals_result = await self.db.execute(query)
        evals = evals_result.scalars().all()

        if not evals:
            return AggregationResponse(
                id=None,
                tenant_id=tenant_id,
                terminal_id=terminal_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                slot_count=0,
                avg_overall=None,
                avg_sentiment=None,
                avg_politeness=None,
                avg_compliance=None,
                avg_resolution=None,
                avg_upselling=None,
                avg_response_time=None,
                avg_honesty=None,
                unclear_count=0,
                flag_counts={},
                computed_at=datetime.now(UTC),
            )

        def avg_score(field_name: str) -> float | None:
            values = [float(getattr(e, field_name)) for e in evals if getattr(e, field_name) is not None]
            return round(sum(values) / len(values), 2) if values else None

        flag_counts: dict[str, int] = {}
        for e in evals:
            if e.flags:
                for f in e.flags:
                    flag_counts[f] = flag_counts.get(f, 0) + 1

        unclear_count = sum(1 for e in evals if e.is_unclear)

        result = await self.db.execute(
            select(AggregatedEvaluation).where(
                AggregatedEvaluation.tenant_id == tid,
                AggregatedEvaluation.period_type == period_type,
                AggregatedEvaluation.period_start == period_start,
            )
        )
        agg = result.scalar_one_or_none()

        if agg is None:
            agg = AggregatedEvaluation(
                tenant_id=tid,
                terminal_id=UUID(terminal_id) if terminal_id else None,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(agg)

        agg.slot_count = len(evals)
        agg.avg_overall = avg_score("score_overall")
        agg.avg_sentiment = avg_score("score_sentiment")
        agg.avg_politeness = avg_score("score_politeness")
        agg.avg_compliance = avg_score("score_compliance")
        agg.avg_resolution = avg_score("score_resolution")
        agg.avg_upselling = avg_score("score_upselling")
        agg.avg_response_time = avg_score("score_response_time")
        agg.avg_honesty = avg_score("score_honesty")
        agg.unclear_count = unclear_count
        agg.flag_counts = flag_counts
        agg.computed_at = datetime.now(UTC)
        await self.db.flush()

        return AggregationResponse(
            id=str(agg.id),
            tenant_id=str(agg.tenant_id),
            terminal_id=str(agg.terminal_id) if agg.terminal_id else None,
            period_type=agg.period_type,
            period_start=agg.period_start,
            period_end=agg.period_end,
            slot_count=agg.slot_count,
            avg_overall=float(agg.avg_overall) if agg.avg_overall is not None else None,
            avg_sentiment=float(agg.avg_sentiment) if agg.avg_sentiment is not None else None,
            avg_politeness=float(agg.avg_politeness) if agg.avg_politeness is not None else None,
            avg_compliance=float(agg.avg_compliance) if agg.avg_compliance is not None else None,
            avg_resolution=float(agg.avg_resolution) if agg.avg_resolution is not None else None,
            avg_upselling=float(agg.avg_upselling) if agg.avg_upselling is not None else None,
            avg_response_time=float(agg.avg_response_time) if agg.avg_response_time is not None else None,
            avg_honesty=float(agg.avg_honesty) if agg.avg_honesty is not None else None,
            unclear_count=agg.unclear_count,
            flag_counts=agg.flag_counts,
            computed_at=agg.computed_at,
        )
