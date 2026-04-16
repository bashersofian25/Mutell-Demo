from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.aggregated_evaluation import AggregatedEvaluation
from app.models.evaluation import Evaluation
from app.models.tenant import Tenant
from app.workers.celery_app import celery_app
from app.workers.db import get_sync_engine

logger = structlog.get_logger()


def _compute_period(
    db: Session,
    tenant_id: UUID,
    period_type: str,
    period_start: datetime,
    period_end: datetime,
) -> None:
    query = select(Evaluation).where(
        Evaluation.tenant_id == tenant_id,
        Evaluation.created_at >= period_start,
        Evaluation.created_at < period_end,
    )
    evals = db.execute(query).scalars().all()

    if not evals:
        return

    def avg_score(field_name: str) -> float | None:
        values = [float(getattr(e, field_name)) for e in evals if getattr(e, field_name) is not None]
        return round(sum(values) / len(values), 2) if values else None

    flag_counts: dict[str, int] = {}
    for e in evals:
        if e.flags:
            for f in e.flags:
                flag_counts[f] = flag_counts.get(f, 0) + 1

    unclear_count = sum(1 for e in evals if e.is_unclear)

    existing = db.execute(
        select(AggregatedEvaluation).where(
            AggregatedEvaluation.tenant_id == tenant_id,
            AggregatedEvaluation.period_type == period_type,
            AggregatedEvaluation.period_start == period_start,
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = AggregatedEvaluation(
            tenant_id=tenant_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
        )
        db.add(existing)

    existing.slot_count = len(evals)
    existing.avg_overall = avg_score("score_overall")
    existing.avg_sentiment = avg_score("score_sentiment")
    existing.avg_politeness = avg_score("score_politeness")
    existing.avg_compliance = avg_score("score_compliance")
    existing.avg_resolution = avg_score("score_resolution")
    existing.avg_upselling = avg_score("score_upselling")
    existing.avg_response_time = avg_score("score_response_time")
    existing.avg_honesty = avg_score("score_honesty")
    existing.unclear_count = unclear_count
    existing.flag_counts = flag_counts
    existing.computed_at = datetime.now(UTC)
    db.flush()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def compute_aggregations(self) -> None:
    logger.info("compute_aggregations_cron_started")
    try:
        engine = get_sync_engine()
        with Session(engine) as db:
            tenants = db.execute(
                select(Tenant).where(Tenant.status == "active")
            ).scalars().all()

            now = datetime.now(UTC)

            for tenant in tenants:
                try:
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    _compute_period(db, tenant.id, "day", today_start, now)

                    hour_start = now.replace(minute=0, second=0, microsecond=0)
                    _compute_period(db, tenant.id, "hour", hour_start, now)

                    week_start = now - timedelta(days=now.weekday())
                    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                    _compute_period(db, tenant.id, "week", week_start, now)

                    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    _compute_period(db, tenant.id, "month", month_start, now)

                    db.commit()

                except Exception as e:
                    logger.error("aggregation_tenant_error", tenant_id=str(tenant.id), error=str(e))
                    db.rollback()

            logger.info("compute_aggregations_cron_completed")

    except Exception as e:
        logger.error("compute_aggregations_cron_failed", error=str(e))
        raise self.retry(exc=e)


@celery_app.task
def compute_aggregations_for_tenant(tenant_id: str) -> None:
    logger.info("compute_aggregations_for_tenant", tenant_id=tenant_id)
    engine = get_sync_engine()
    with Session(engine) as db:
        tid = UUID(tenant_id)
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        _compute_period(db, tid, "day", today_start, now)
        db.commit()
