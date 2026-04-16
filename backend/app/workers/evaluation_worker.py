import asyncio
import traceback
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import func, select

from app.ai_engine.adapters.base import EvaluationResult
from app.ai_engine.factory import get_adapter
from app.ai_engine.prompt_builder import build_system_prompt, build_user_prompt
from app.core.config import settings
from app.core.crypto import decrypt_api_key
from app.models.evaluation import Evaluation
from app.models.slot import Slot
from app.models.tenant import Tenant
from app.models.tenant_ai_config import TenantAIConfig
from app.models.ai_provider import AIProvider
from app.models.user import User
from app.workers.celery_app import celery_app
from app.workers.db import get_sync_engine
from app.workers.eval_semaphore import acquire_eval_slot, release_eval_slot, check_eval_dedup, clear_eval_dedup, acquire_user_eval_slot, release_user_eval_slot

logger = structlog.get_logger()


def _run_async(coro):
    return asyncio.run(coro)


def _fail(db, slot, reason, **ctx):
    logger.error("evaluation_failed", slot_id=str(slot.id), reason=reason, **ctx)
    slot.status = "failed"
    db.commit()


def _requeue(db, slot, reason, **ctx):
    logger.info("evaluation_requeued", slot_id=str(slot.id), reason=reason, **ctx)
    slot.status = "queued"
    db.commit()


def _get_effective_max_concurrent(tenant: Tenant) -> int:
    if tenant.max_concurrent_evaluations is not None:
        return tenant.max_concurrent_evaluations
    if tenant.plan is not None:
        return tenant.plan.max_concurrent_evaluations
    return 2


async def _evaluate_slot(slot_id: str, user_id: str | None = None) -> None:
    from sqlalchemy.orm import Session

    engine = get_sync_engine()
    with Session(engine) as db:
        result = db.execute(select(Slot).where(Slot.id == UUID(slot_id)))
        slot = result.scalar_one_or_none()
        if slot is None:
            logger.error("slot_not_found", slot_id=slot_id)
            return

        logger.info(
            "evaluation_started",
            slot_id=slot_id,
            tenant_id=str(slot.tenant_id),
            terminal_id=str(slot.terminal_id) if slot.terminal_id else None,
            user_id=user_id,
            word_count=slot.word_count,
            status=slot.status,
        )

        if slot.status not in ("pending", "failed", "queued"):
            logger.info("slot_already_evaluated", slot_id=slot_id, status=slot.status)
            return

        if not check_eval_dedup(slot_id):
            return

        tenant_result = db.execute(
            select(Tenant).where(Tenant.id == slot.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant is None:
            _fail(db, slot, "tenant_not_found")
            return

        max_concurrent = _get_effective_max_concurrent(tenant)

        user_max_concurrent = None
        if user_id:
            user_result = db.execute(select(User).where(User.id == UUID(user_id)))
            triggering_user = user_result.scalar_one_or_none()
            if triggering_user and triggering_user.max_concurrent_evaluations is not None:
                user_max_concurrent = triggering_user.max_concurrent_evaluations

        old_eval_result = db.execute(
            select(Evaluation).where(Evaluation.slot_id == slot.id)
        )
        old_eval = old_eval_result.scalar_one_or_none()
        if old_eval:
            db.delete(old_eval)
            db.flush()

        slot.status = "pending"
        db.flush()

        acquired = acquire_eval_slot(
            tenant_id=str(slot.tenant_id),
            slot_id=slot_id,
            max_concurrent=max_concurrent,
        )
        if not acquired:
            _requeue(db, slot, "concurrency_limit_reached", max_concurrent=max_concurrent)
            clear_eval_dedup(slot_id)
            return

        user_acquired = False
        if user_id and user_max_concurrent is not None:
            user_acquired = acquire_user_eval_slot(
                user_id=user_id,
                slot_id=slot_id,
                max_concurrent=user_max_concurrent,
            )
            if not user_acquired:
                release_eval_slot(tenant_id=str(slot.tenant_id), slot_id=slot_id)
                _requeue(db, slot, "user_concurrency_limit_reached", user_id=user_id, max_concurrent=user_max_concurrent)
                clear_eval_dedup(slot_id)
                return

        try:
            slot.status = "processing"
            db.flush()

            config_result = db.execute(
                select(TenantAIConfig)
                .where(TenantAIConfig.tenant_id == slot.tenant_id, TenantAIConfig.is_default.is_(True))
            )
            ai_config = config_result.scalar_one_or_none()

            if ai_config is None:
                all_configs = db.execute(
                    select(TenantAIConfig.id, TenantAIConfig.provider_id, TenantAIConfig.model_id, TenantAIConfig.is_default)
                    .where(TenantAIConfig.tenant_id == slot.tenant_id)
                ).all()
                _fail(db, slot, "no_ai_config",
                      tenant_id=str(slot.tenant_id),
                      existing_configs=[{"id": str(c.id), "provider_id": str(c.provider_id), "model_id": c.model_id, "is_default": c.is_default} for c in all_configs])
                return

            logger.info(
                "ai_config_found",
                slot_id=slot_id,
                config_id=str(ai_config.id),
                provider_id=str(ai_config.provider_id),
                model_id=ai_config.model_id,
                has_custom_prompt=bool(ai_config.custom_prompt),
                has_tenant_api_key=bool(ai_config.api_key_enc),
            )

            provider_result = db.execute(select(AIProvider).where(AIProvider.id == ai_config.provider_id))
            provider = provider_result.scalar_one_or_none()
            if provider is None:
                _fail(db, slot, "provider_not_found", provider_id=str(ai_config.provider_id))
                return
            if not provider.is_active:
                _fail(db, slot, "provider_inactive",
                      provider_id=str(provider.id),
                      provider_slug=provider.slug,
                      provider_name=provider.display_name)
                return

            logger.info("provider_resolved", slot_id=slot_id, provider=provider.slug, has_provider_api_key=bool(provider.api_key_enc))

            api_key = None
            api_key_source = None
            try:
                if ai_config.api_key_enc:
                    api_key = decrypt_api_key(ai_config.api_key_enc)
                    api_key_source = "tenant_config"
                elif provider.api_key_enc:
                    api_key = decrypt_api_key(provider.api_key_enc)
                    api_key_source = "provider_default"
                else:
                    _fail(db, slot, "no_api_key_available",
                          tenant_id=str(slot.tenant_id),
                          config_id=str(ai_config.id),
                          provider=provider.slug,
                          hint="Set an API key in Settings > AI or ask your admin to set one on the AI provider")
                    return
            except Exception as decrypt_err:
                _fail(db, slot, "api_key_decryption_failed",
                      error=str(decrypt_err),
                      api_key_source=api_key_source,
                      traceback=traceback.format_exc())
                return

            logger.info("api_key_decrypted", slot_id=slot_id, source=api_key_source, key_preview=api_key[:8] + "..." + api_key[-4:])

            system_prompt = build_system_prompt(custom_prompt=ai_config.custom_prompt)
            user_prompt = build_user_prompt(slot.raw_text)

            logger.info("calling_ai", slot_id=slot_id, provider=provider.slug, model=ai_config.model_id)

            try:
                adapter = get_adapter(provider.slug)
                eval_result: EvaluationResult = await adapter.evaluate(
                    raw_text=slot.raw_text,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=ai_config.model_id,
                    api_key=api_key,
                    base_url=provider.base_url,
                )
            except Exception as e:
                import httpx as _httpx
                is_rate_limit = isinstance(e, _httpx.HTTPStatusError) and e.response.status_code == 429
                if is_rate_limit:
                    _requeue(db, slot, "api_rate_limited",
                             provider=provider.slug,
                             model=ai_config.model_id)
                else:
                    _fail(db, slot, "ai_evaluation_failed",
                          provider=provider.slug,
                          model=ai_config.model_id,
                          error=str(e),
                          error_type=type(e).__name__,
                          traceback=traceback.format_exc())
                return

            unclear_count = len(eval_result.unclear_items) if eval_result.unclear_items else 0
            is_unclear = unclear_count > 3

            evaluation = Evaluation(
                slot_id=slot.id,
                tenant_id=slot.tenant_id,
                ai_provider=provider.slug,
                ai_model=ai_config.model_id,
                score_overall=eval_result.overall,
                score_sentiment=eval_result.sentiment,
                score_politeness=eval_result.politeness,
                score_compliance=eval_result.compliance,
                score_resolution=eval_result.resolution,
                score_upselling=eval_result.upselling,
                score_response_time=eval_result.response_time,
                score_honesty=eval_result.honesty,
                sentiment_label=eval_result.sentiment_label,
                language_detected=eval_result.language_detected,
                summary=eval_result.summary,
                strengths=eval_result.strengths or [],
                weaknesses=eval_result.weaknesses or [],
                recommendations=eval_result.recommendations or [],
                unclear_items=eval_result.unclear_items or [],
                flags=eval_result.flags or [],
                unavailable_items=eval_result.unavailable_items or [],
                swearing_count=eval_result.swearing_count,
                swearing_instances=eval_result.swearing_instances or [],
                off_topic_count=eval_result.off_topic_count,
                off_topic_segments=eval_result.off_topic_segments or [],
                speaker_segments=eval_result.speaker_segments or [],
                raw_response=eval_result.raw_response,
                tokens_used=eval_result.tokens_used,
                evaluation_duration_ms=eval_result.duration_ms,
                is_unclear=is_unclear,
            )
            db.add(evaluation)

            tags: list[str] = []
            if eval_result.unavailable_items:
                tags.append("items_unavailable")
            if eval_result.swearing_count and eval_result.swearing_count > 0:
                tags.append("swearing")
            if eval_result.off_topic_count and eval_result.off_topic_count > 0:
                tags.append("off_topic")
            if eval_result.politeness is not None and eval_result.politeness < 50:
                tags.append("low_politeness")
            if eval_result.flags:
                tags.extend(eval_result.flags)
            slot.tags = list(set(tags))

            new_status = "unclear" if is_unclear else "evaluated"
            slot.status = new_status
            slot.language = eval_result.language_detected
            db.commit()

            logger.info(
                "evaluation_complete",
                slot_id=slot_id,
                status=new_status,
                provider=provider.slug,
                model=ai_config.model_id,
                overall=eval_result.overall,
                sentiment=eval_result.sentiment,
                language=eval_result.language_detected,
                duration_ms=eval_result.duration_ms,
                tokens_used=eval_result.tokens_used,
                unclear_items=unclear_count,
            )

            try:
                from app.workers.aggregation_worker import compute_aggregations_for_tenant
                compute_aggregations_for_tenant.delay(str(slot.tenant_id))
            except Exception:
                pass
        finally:
            release_eval_slot(tenant_id=str(slot.tenant_id), slot_id=slot_id)
            if user_id and user_acquired:
                release_user_eval_slot(user_id=user_id, slot_id=slot_id)
            clear_eval_dedup(slot_id)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def evaluate_slot(self, slot_id: str, user_id: str | None = None) -> None:
    logger.info("evaluate_slot_task", slot_id=slot_id, user_id=user_id, attempt=self.request.retries)
    try:
        _run_async(_evaluate_slot(slot_id, user_id))
    except Exception as exc:
        logger.error("evaluate_slot_unhandled", slot_id=slot_id, error=str(exc), traceback=traceback.format_exc())
        raise self.retry(exc=exc)
