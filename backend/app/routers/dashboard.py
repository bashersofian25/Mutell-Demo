from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.evaluation import Evaluation
from app.models.slot import Slot
from app.models.terminal import Terminal
from app.models.user import User

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    tid = UUID(str(user.tenant_id))

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    slot_counts_q = await db.execute(
        select(
            func.count().filter(Slot.created_at >= today_start).label("slots_today"),
            func.count().label("slots_week"),
            func.count().filter(Slot.status.in_(["evaluated", "unclear"]), Slot.created_at >= today_start).label("evaluated_today"),
            func.count().filter(Slot.status == "failed", Slot.created_at >= today_start).label("failed_today"),
            func.count().filter(Slot.status.in_(["pending", "processing"])).label("pending_evaluations"),
        )
        .where(Slot.tenant_id == tid, Slot.created_at >= week_start)
    )
    slot_row = slot_counts_q.one()

    active_terminals_q = await db.execute(
        select(func.count()).where(Terminal.tenant_id == tid, Terminal.status == "active")
    )
    active_terminals = active_terminals_q.scalar() or 0

    avg_score_q = await db.execute(
        select(
            func.avg(Evaluation.score_overall).filter(Evaluation.created_at >= week_start).label("avg_week"),
            func.avg(Evaluation.score_overall).filter(Evaluation.created_at >= month_start).label("avg_month"),
        )
        .where(Evaluation.tenant_id == tid)
    )
    score_row = avg_score_q.one()

    avg_score = round(float(score_row.avg_week), 1) if score_row.avg_week else None
    month_avg = round(float(score_row.avg_month), 1) if score_row.avg_month else None

    return {
        "success": True,
        "data": {
            "slots_today": slot_row.slots_today,
            "slots_week": slot_row.slots_week,
            "evaluated_today": slot_row.evaluated_today,
            "failed_today": slot_row.failed_today,
            "pending_evaluations": slot_row.pending_evaluations,
            "active_terminals": active_terminals,
            "avg_score_week": avg_score,
            "avg_score_month": month_avg,
        },
    }


@router.get("/trends")
async def dashboard_trends(
    days: int = Query(14, ge=1, le=90),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    tid = UUID(str(user.tenant_id))
    since = datetime.now(UTC) - timedelta(days=days)

    day_col = func.date_trunc("day", Slot.created_at).label("date")
    rows = await db.execute(
        select(
            day_col,
            func.count().label("slot_count"),
        )
        .where(Slot.tenant_id == tid, Slot.created_at >= since)
        .group_by(day_col)
        .order_by(day_col)
    )
    slot_counts = {r.date.date(): r.slot_count for r in rows.all()}

    score_day_col = func.date_trunc("day", Evaluation.created_at).label("date")
    score_rows = await db.execute(
        select(
            score_day_col,
            func.avg(Evaluation.score_overall).label("avg_score"),
        )
        .where(Evaluation.tenant_id == tid, Evaluation.created_at >= since)
        .group_by(score_day_col)
        .order_by(score_day_col)
    )
    score_map = {r.date.date(): round(float(r.avg_score), 1) if r.avg_score else None for r in score_rows.all()}

    all_dates = sorted(set(list(slot_counts.keys()) + list(score_map.keys())))
    items = [
        {
            "date": d.isoformat(),
            "avg_score": score_map.get(d),
            "slot_count": slot_counts.get(d, 0),
        }
        for d in all_dates
    ]

    return {"items": items}
