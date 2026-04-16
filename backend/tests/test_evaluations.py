from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.slot import Slot

EVALUATIONS_URL = "/api/v1/evaluations"


async def _create_slot_with_eval(
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
    **eval_overrides,
) -> tuple[Slot, Evaluation]:
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime(2025, 1, 15, 9, 30, tzinfo=timezone.utc),
        ended_at=datetime(2025, 1, 15, 9, 35, tzinfo=timezone.utc),
        raw_text="test interaction text",
        status="completed",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    eval_defaults = dict(
        slot_id=slot.id,
        tenant_id=test_tenant.id,
        ai_provider="openai",
        ai_model="gpt-4o",
        score_overall=85.5,
        score_sentiment=90.0,
        score_politeness=88.0,
        score_compliance=95.0,
        score_resolution=82.0,
        score_upselling=70.0,
        score_response_time=75.0,
        score_honesty=92.0,
        sentiment_label="positive",
        language_detected="en",
        summary="Good interaction",
        strengths=["polite", "efficient"],
        weaknesses=["could upsell"],
        recommendations=["offer loyalty program"],
        unclear_items=[],
        flags=[],
        tokens_used=250,
        evaluation_duration_ms=1200,
        is_unclear=False,
    )
    eval_defaults.update(eval_overrides)
    evaluation = Evaluation(**eval_defaults)
    db_session.add(evaluation)
    await db_session.flush()
    return slot, evaluation


@pytest.mark.asyncio
async def test_get_evaluation_not_found(tenant_admin_client: AsyncClient):
    random_slot_id = str(uuid4())
    response = await tenant_admin_client.get(f"{EVALUATIONS_URL}/{random_slot_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_evaluation_success(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot, evaluation = await _create_slot_with_eval(db_session, test_tenant, test_terminal)

    response = await tenant_admin_client.get(f"{EVALUATIONS_URL}/{slot.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["slot_id"] == str(slot.id)
    assert data["tenant_id"] == str(test_tenant.id)
    assert data["ai_provider"] == "openai"
    assert data["ai_model"] == "gpt-4o"
    assert data["score_overall"] == 85.5
    assert data["sentiment_label"] == "positive"
    assert data["language_detected"] == "en"
    assert data["summary"] == "Good interaction"
    assert data["strengths"] == ["polite", "efficient"]
    assert data["weaknesses"] == ["could upsell"]
    assert data["recommendations"] == ["offer loyalty program"]
    assert data["tokens_used"] == 250
    assert data["evaluation_duration_ms"] == 1200
    assert data["is_unclear"] is False


@pytest.mark.asyncio
async def test_get_evaluation_includes_all_score_fields(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot, _ = await _create_slot_with_eval(db_session, test_tenant, test_terminal)

    response = await tenant_admin_client.get(f"{EVALUATIONS_URL}/{slot.id}")
    assert response.status_code == 200
    data = response.json()
    score_fields = [
        "score_overall",
        "score_sentiment",
        "score_politeness",
        "score_compliance",
        "score_resolution",
        "score_upselling",
        "score_response_time",
        "score_honesty",
    ]
    for field in score_fields:
        assert field in data, f"Missing score field: {field}"
        assert isinstance(data[field], (int, float)), f"{field} should be numeric"


@pytest.mark.asyncio
async def test_get_evaluation_cross_tenant_forbidden(
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot, _ = await _create_slot_with_eval(db_session, test_tenant, test_terminal)

    response = await second_tenant_admin_client.get(f"{EVALUATIONS_URL}/{slot.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_evaluation_unauthenticated(client: AsyncClient):
    fake_id = str(uuid4())
    response = await client.get(f"{EVALUATIONS_URL}/{fake_id}")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_evaluation_viewer_allowed(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot, _ = await _create_slot_with_eval(db_session, test_tenant, test_terminal)

    response = await viewer_client.get(f"{EVALUATIONS_URL}/{slot.id}")
    assert response.status_code == 200
    assert response.json()["slot_id"] == str(slot.id)
