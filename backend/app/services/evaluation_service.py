from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationResponse


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_evaluation(self, tenant_id: str, slot_id: str) -> EvaluationResponse | None:
        result = await self.db.execute(
            select(Evaluation).where(
                Evaluation.slot_id == UUID(slot_id),
                Evaluation.tenant_id == UUID(tenant_id),
            )
        )
        evaluation = result.scalar_one_or_none()
        if evaluation is None:
            return None

        return EvaluationResponse(
            id=str(evaluation.id),
            slot_id=str(evaluation.slot_id),
            tenant_id=str(evaluation.tenant_id),
            ai_provider=evaluation.ai_provider,
            ai_model=evaluation.ai_model,
            prompt_version=evaluation.prompt_version,
            score_overall=float(evaluation.score_overall) if evaluation.score_overall is not None else None,
            score_sentiment=float(evaluation.score_sentiment) if evaluation.score_sentiment is not None else None,
            score_politeness=float(evaluation.score_politeness) if evaluation.score_politeness is not None else None,
            score_compliance=float(evaluation.score_compliance) if evaluation.score_compliance is not None else None,
            score_resolution=float(evaluation.score_resolution) if evaluation.score_resolution is not None else None,
            score_upselling=float(evaluation.score_upselling) if evaluation.score_upselling is not None else None,
            score_response_time=float(evaluation.score_response_time) if evaluation.score_response_time is not None else None,
            score_honesty=float(evaluation.score_honesty) if evaluation.score_honesty is not None else None,
            sentiment_label=evaluation.sentiment_label,
            language_detected=evaluation.language_detected,
            summary=evaluation.summary,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            recommendations=evaluation.recommendations,
            unclear_items=evaluation.unclear_items,
            flags=evaluation.flags,
            tokens_used=evaluation.tokens_used,
            evaluation_duration_ms=evaluation.evaluation_duration_ms,
            is_unclear=evaluation.is_unclear,
            created_at=evaluation.created_at,
        )
