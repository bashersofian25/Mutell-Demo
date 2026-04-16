import time

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.slot import Slot
from app.models.tenant import Tenant
from app.models.user import User
from app.workers.celery_app import celery_app
from app.workers.db import get_sync_engine
from app.workers.eval_semaphore import (
    get_tenant_concurrent_count,
    get_user_concurrent_count,
    clear_eval_dedup,
)

logger = structlog.get_logger()

SCHEDULER_DEDUP_TTL = 30
RETRY_DELAY_SECONDS = 10


def _get_effective_max_concurrent(tenant: Tenant) -> int:
    if tenant.max_concurrent_evaluations is not None:
        return tenant.max_concurrent_evaluations
    if tenant.plan is not None:
        return tenant.plan.max_concurrent_evaluations
    return 2


def _acquire_scheduler_lock() -> bool:
    import redis
    from app.core.config import settings

    r = redis.from_url(settings.REDIS_URL)
    key = "eval_scheduler:lock"
    acquired = r.set(key, "1", nx=True, ex=SCHEDULER_DEDUP_TTL)
    r.close()
    return bool(acquired)


@celery_app.task(bind=True, max_retries=None)
def schedule_pending_evaluations(self) -> None:
    from sqlalchemy.orm import Session
    from app.workers.evaluation_worker import evaluate_slot

    if not _acquire_scheduler_lock():
        logger.debug("scheduler_skipped_locked")
        return

    engine = get_sync_engine()
    with Session(engine) as db:
        result = db.execute(
            select(Slot)
            .where(Slot.status.in_(["pending", "queued"]))
            .order_by(Slot.created_at.asc())
        )
        pending_slots = result.scalars().all()

        if not pending_slots:
            return

        logger.info("scheduler_run", pending_count=len(pending_slots))

        tenant_cache: dict = {}
        user_cache: dict = {}
        dispatched = 0
        skipped = 0

        for slot in pending_slots:
            tid = str(slot.tenant_id)

            if tid not in tenant_cache:
                t = db.execute(
                    select(Tenant).where(Tenant.id == slot.tenant_id).options(selectinload(Tenant.plan))
                ).scalar_one_or_none()
                if t is None:
                    skipped += 1
                    continue
                tenant_cache[tid] = {
                    "max": _get_effective_max_concurrent(t),
                    "current": get_tenant_concurrent_count(tid),
                    "dispatched": 0,
                }

            tc = tenant_cache[tid]
            if tc["current"] + tc["dispatched"] >= tc["max"]:
                skipped += 1
                continue

            if slot.triggered_by_user_id:
                uid = str(slot.triggered_by_user_id)
                if uid not in user_cache:
                    u = db.execute(
                        select(User).where(User.id == slot.triggered_by_user_id)
                    ).scalar_one_or_none()
                    user_cache[uid] = {
                        "max": u.max_concurrent_evaluations if u else 1,
                        "current": get_user_concurrent_count(uid),
                        "dispatched": 0,
                    }
                uc = user_cache[uid]
                if uc["current"] + uc["dispatched"] >= uc["max"]:
                    skipped += 1
                    continue
                uc["dispatched"] += 1

            clear_eval_dedup(str(slot.id))
            slot.status = "pending"
            db.flush()

            evaluate_slot.delay(
                str(slot.id),
                str(slot.triggered_by_user_id) if slot.triggered_by_user_id else None,
            )
            tc["dispatched"] += 1
            dispatched += 1

        logger.info(
            "scheduler_dispatched",
            dispatched=dispatched,
            skipped=skipped,
            total=len(pending_slots),
        )

        if skipped > 0:
            logger.info("scheduler_retrigger", retry_in=RETRY_DELAY_SECONDS, skipped=skipped)
            schedule_pending_evaluations.apply_async(countdown=RETRY_DELAY_SECONDS)
