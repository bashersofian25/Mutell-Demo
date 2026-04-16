import structlog
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.plan import Plan
from app.models.slot import Slot
from app.models.tenant import Tenant
from app.models.evaluation import Evaluation
from app.schemas.slot import SlotAccepted, SlotCreate, SlotDetail, SlotListResponse, SlotResponse

logger = structlog.get_logger()


class SlotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_tenant_with_plan(self, tenant_id: UUID) -> Tenant | None:
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id).options(selectinload(Tenant.plan))
        )
        return result.scalar_one_or_none()

    async def _check_plan_quota(self, tenant_id: UUID) -> bool:
        tenant = await self._get_tenant_with_plan(tenant_id)
        if tenant is None or tenant.plan is None:
            return False

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        count_result = await self.db.execute(
            select(func.count()).select_from(Slot).where(
                Slot.tenant_id == tenant_id,
                Slot.created_at >= today_start,
            )
        )
        today_count = count_result.scalar() or 0
        return today_count < tenant.plan.max_slots_per_day

    async def create_slot(
        self,
        tenant_id: str,
        terminal_id: str | None,
        body: SlotCreate,
    ) -> SlotAccepted:
        tid = UUID(tenant_id)

        if not await self._check_plan_quota(tid):
            raise ValueError("plan_limit_exceeded")

        raw_text_clean = body.raw_text.replace("\x00", "").strip()
        word_count = len(raw_text_clean.split()) if raw_text_clean else 0

        slot = Slot(
            tenant_id=tid,
            terminal_id=UUID(terminal_id) if terminal_id else None,
            started_at=body.started_at,
            ended_at=body.ended_at,
            raw_text=raw_text_clean,
            word_count=word_count,
            metadata_=body.metadata or {},
            status="pending",
        )
        self.db.add(slot)
        await self.db.flush()

        try:
            from app.workers.eval_scheduler import schedule_pending_evaluations
            schedule_pending_evaluations.delay()
        except Exception as e:
            logger.warning("scheduler_dispatch_failed", slot_id=str(slot.id), error=str(e))

        tenant = await self._get_tenant_with_plan(tid)

        return SlotAccepted(
            slot_id=str(slot.id),
            status="accepted",
            config={"slot_duration_secs": tenant.slot_duration_secs if tenant else 300},
        )

    async def list_slots(
        self,
        tenant_id: str,
        page: int,
        per_page: int,
        terminal_id: str | None = None,
        status_filter: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> SlotListResponse:
        query = select(Slot).where(Slot.tenant_id == UUID(tenant_id))

        if terminal_id:
            query = query.where(Slot.terminal_id == UUID(terminal_id))
        if status_filter:
            query = query.where(Slot.status == status_filter)
        if date_from:
            try:
                query = query.where(Slot.started_at >= datetime.fromisoformat(date_from))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid date_from format: {date_from}")
        if date_to:
            try:
                query = query.where(Slot.ended_at <= datetime.fromisoformat(date_to))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid date_to format: {date_to}")

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(Slot.started_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        slots = result.scalars().all()

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
                    metadata=s.metadata_,
                    created_at=s.created_at,
                )
                for s in slots
            ],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_slot(self, tenant_id: str, slot_id: str) -> SlotDetail | None:
        result = await self.db.execute(
            select(Slot).where(Slot.id == UUID(slot_id), Slot.tenant_id == UUID(tenant_id))
        )
        slot = result.scalar_one_or_none()
        if slot is None:
            return None

        eval_result = await self.db.execute(
            select(Evaluation).where(Evaluation.slot_id == slot.id)
        )
        evaluation = eval_result.scalar_one_or_none()

        from app.schemas.evaluation import EvaluationResponse
        eval_response = None
        if evaluation:
            eval_response = EvaluationResponse.model_validate(evaluation, from_attributes=True)

        return SlotDetail(
            id=str(slot.id),
            terminal_id=str(slot.terminal_id) if slot.terminal_id else None,
            tenant_id=str(slot.tenant_id),
            started_at=slot.started_at,
            ended_at=slot.ended_at,
            duration_secs=slot.duration_secs,
            language=slot.language,
            word_count=slot.word_count,
            status=slot.status,
            metadata=slot.metadata_,
            created_at=slot.created_at,
            raw_text=slot.raw_text,
            evaluation=eval_response,
        )

    async def re_evaluate(self, tenant_id: str, slot_id: str, user_id: str | None = None) -> bool:
        result = await self.db.execute(
            select(Slot).where(Slot.id == UUID(slot_id), Slot.tenant_id == UUID(tenant_id))
        )
        slot = result.scalar_one_or_none()
        if slot is None:
            return False

        eval_result = await self.db.execute(
            select(Evaluation).where(Evaluation.slot_id == slot.id)
        )
        old_eval = eval_result.scalar_one_or_none()
        if old_eval:
            await self.db.delete(old_eval)

        slot.status = "pending"
        if user_id:
            slot.triggered_by_user_id = UUID(user_id)
        await self.db.flush()

        try:
            from app.workers.eval_scheduler import schedule_pending_evaluations
            schedule_pending_evaluations.delay()
        except Exception as e:
            logger.warning("scheduler_dispatch_failed", slot_id=str(slot.id), error=str(e))

        return True
