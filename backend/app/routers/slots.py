from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_terminal, get_current_user
from app.models.evaluation import Evaluation
from app.models.slot import Slot
from app.models.terminal import Terminal
from app.models.user import User
from app.schemas.slot import (
    BulkReEvaluateRequest,
    BulkReEvaluateResponse,
    ReEvaluateResponse,
    SlotAccepted,
    SlotCreate,
    SlotDetail,
    SlotListResponse,
)
from app.services.slot_service import SlotService

router = APIRouter()


@router.post("", status_code=http_status.HTTP_202_ACCEPTED, response_model=SlotAccepted)
async def create_slot(
    body: SlotCreate,
    terminal: Terminal = Depends(get_current_terminal),
    db: AsyncSession = Depends(get_db),
):
    svc = SlotService(db)
    try:
        return await svc.create_slot(
            tenant_id=str(terminal.tenant_id),
            terminal_id=str(terminal.id),
            body=body,
        )
    except ValueError as e:
        if str(e) == "plan_limit_exceeded":
            raise HTTPException(
                status_code=http_status.HTTP_402_PAYMENT_REQUIRED,
                detail="Daily slot quota exceeded",
            )
        raise


@router.get("", response_model=SlotListResponse)
async def list_slots(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    terminal_id: UUID | None = None,
    slot_status: str | None = Query(None, alias="status"),
    date_from: str | None = None,
    date_to: str | None = None,
    min_score: float | None = Query(None, ge=0, le=100),
    max_score: float | None = Query(None, ge=0, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    tid = UUID(str(user.tenant_id))

    base_query = select(Slot.id).where(Slot.tenant_id == tid)

    if terminal_id:
        base_query = base_query.where(Slot.terminal_id == terminal_id)
    if slot_status:
        base_query = base_query.where(Slot.status == slot_status)
    if date_from:
        try:
            base_query = base_query.where(Slot.started_at >= datetime.fromisoformat(date_from))
        except (ValueError, TypeError):
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_from: {date_from}")
    if date_to:
        try:
            base_query = base_query.where(Slot.ended_at <= datetime.fromisoformat(date_to))
        except (ValueError, TypeError):
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_to: {date_to}")

    if min_score is not None or max_score is not None:
        eval_subq = select(Evaluation.slot_id).where(Evaluation.tenant_id == tid)
        if min_score is not None:
            eval_subq = eval_subq.where(Evaluation.score_overall >= min_score)
        if max_score is not None:
            eval_subq = eval_subq.where(Evaluation.score_overall <= max_score)
        base_query = base_query.where(Slot.id.in_(eval_subq))

    from sqlalchemy import func as _func
    count_q = select(_func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    slot_ids_query = base_query.order_by(Slot.started_at.desc()).offset((page - 1) * per_page).limit(per_page)
    id_result = await db.execute(slot_ids_query)
    slot_ids = [row[0] for row in id_result.all()]

    if not slot_ids:
        return SlotListResponse(items=[], total=0, page=page, per_page=per_page)

    slots_query = select(Slot).where(Slot.id.in_(slot_ids)).order_by(Slot.started_at.desc())
    slots_result = await db.execute(slots_query)
    slots = slots_result.scalars().all()

    eval_result = await db.execute(
        select(Evaluation.slot_id, Evaluation.score_overall).where(Evaluation.slot_id.in_(slot_ids))
    )
    score_map: dict = {row[0]: float(row[1]) if row[1] is not None else None for row in eval_result.all()}

    from app.schemas.slot import SlotResponse
    return SlotListResponse(
        items=[
            SlotResponse(
                id=str(s.id),
                terminal_id=str(s.terminal_id) if s.terminal_id else None,
                tenant_id=str(s.tenant_id),
                started_at=s.started_at,
                ended_at=s.ended_at,
                duration_secs=s.duration_secs,
                language=s.language,
                word_count=s.word_count,
                status=s.status,
                tags=s.tags or [],
                metadata=s.metadata_,
                created_at=s.created_at,
                score_overall=score_map.get(s.id),
            )
            for s in slots
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{slot_id}", response_model=SlotDetail)
async def get_slot(
    slot_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = SlotService(db)
    result = await svc.get_slot(tenant_id=str(user.tenant_id), slot_id=str(slot_id))
    if result is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Slot not found")
    return result


@router.post("/{slot_id}/re-evaluate", response_model=ReEvaluateResponse)
async def re_evaluate_slot(
    slot_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only admins can re-evaluate")

    if not user.tenant_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = SlotService(db)
    success = await svc.re_evaluate(tenant_id=str(user.tenant_id), slot_id=str(slot_id), user_id=str(user.id))
    if not success:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Slot not found")
    return ReEvaluateResponse(slot_id=str(slot_id), status="re-evaluating")


@router.post("/bulk-re-evaluate", response_model=BulkReEvaluateResponse)
async def bulk_re_evaluate(
    body: BulkReEvaluateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin"):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only admins can re-evaluate")

    if not user.tenant_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    from uuid import UUID as _UUID
    from app.models.slot import Slot as SlotModel

    slot_uuids = []
    for sid in body.slot_ids[:100]:
        try:
            slot_uuids.append(_UUID(sid))
        except ValueError:
            continue

    if not slot_uuids:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="No valid slot IDs provided")

    result = await db.execute(
        select(SlotModel).where(
            SlotModel.id.in_(slot_uuids),
            SlotModel.tenant_id == _UUID(str(user.tenant_id)),
        )
    )
    slots = result.scalars().all()

    queued_ids = []
    for slot in slots:
        slot.status = "pending"
        if user.id:
            slot.triggered_by_user_id = user.id
        queued_ids.append(str(slot.id))

    await db.flush()

    try:
        from app.workers.eval_scheduler import schedule_pending_evaluations
        schedule_pending_evaluations.delay()
    except Exception as e:
        import structlog
        structlog.get_logger().warning("scheduler_dispatch_failed", error=str(e))

    return BulkReEvaluateResponse(queued=len(queued_ids), slot_ids=queued_ids)
