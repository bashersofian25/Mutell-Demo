from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.evaluation import Evaluation
from app.models.user import User
from app.schemas.evaluation import EvaluationListResponse, EvaluationResponse

router = APIRouter()


@router.get("", response_model=EvaluationListResponse)
async def list_evaluations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    date_from: str | None = None,
    date_to: str | None = None,
    min_score: float | None = Query(None, ge=0, le=100),
    max_score: float | None = Query(None, ge=0, le=100),
    ai_provider: str | None = None,
    is_unclear: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    from datetime import datetime as dt

    tid = UUID(str(user.tenant_id))
    query = select(Evaluation).where(Evaluation.tenant_id == tid)

    if date_from:
        try:
            query = query.where(Evaluation.created_at >= dt.fromisoformat(date_from))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_from: {date_from}")
    if date_to:
        try:
            query = query.where(Evaluation.created_at <= dt.fromisoformat(date_to))
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date_to: {date_to}")
    if min_score is not None:
        query = query.where(Evaluation.score_overall >= min_score)
    if max_score is not None:
        query = query.where(Evaluation.score_overall <= max_score)
    if ai_provider:
        query = query.where(Evaluation.ai_provider == ai_provider)
    if is_unclear is not None:
        query = query.where(Evaluation.is_unclear == is_unclear)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Evaluation.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    evaluations = result.scalars().all()

    items = []
    for ev in evaluations:
        items.append(EvaluationResponse(
            id=str(ev.id),
            slot_id=str(ev.slot_id),
            tenant_id=str(ev.tenant_id),
            ai_provider=ev.ai_provider,
            ai_model=ev.ai_model,
            prompt_version=ev.prompt_version,
            score_overall=float(ev.score_overall) if ev.score_overall is not None else None,
            score_sentiment=float(ev.score_sentiment) if ev.score_sentiment is not None else None,
            score_politeness=float(ev.score_politeness) if ev.score_politeness is not None else None,
            score_compliance=float(ev.score_compliance) if ev.score_compliance is not None else None,
            score_resolution=float(ev.score_resolution) if ev.score_resolution is not None else None,
            score_upselling=float(ev.score_upselling) if ev.score_upselling is not None else None,
            score_response_time=float(ev.score_response_time) if ev.score_response_time is not None else None,
            score_honesty=float(ev.score_honesty) if ev.score_honesty is not None else None,
            sentiment_label=ev.sentiment_label,
            language_detected=ev.language_detected,
            summary=ev.summary,
            strengths=ev.strengths,
            weaknesses=ev.weaknesses,
            recommendations=ev.recommendations,
            unclear_items=ev.unclear_items,
            flags=ev.flags,
            tokens_used=ev.tokens_used,
            evaluation_duration_ms=ev.evaluation_duration_ms,
            is_unclear=ev.is_unclear,
            created_at=ev.created_at,
        ))

    return EvaluationListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{slot_id}", response_model=EvaluationResponse)
async def get_evaluation(
    slot_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    from app.services.evaluation_service import EvaluationService

    svc = EvaluationService(db)
    result = await svc.get_evaluation(tenant_id=str(user.tenant_id), slot_id=str(slot_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return result
