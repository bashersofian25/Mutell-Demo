"""Cross-cutting security tests: tenant isolation, JWT edge cases, API key validation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.evaluation import Evaluation
from app.models.note import Note
from app.models.slot import Slot

SLOTS_URL = "/api/v1/slots"
NOTES_URL = "/api/v1/notes"
EVALUATIONS_URL = "/api/v1/evaluations"
TERMINALS_URL = "/api/v1/terminals"


# --- Tenant Isolation ---


@pytest.mark.asyncio
async def test_tenant_isolation_slots(
    tenant_admin_client: AsyncClient,
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
    second_tenant,
    second_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="tenant A slot",
        status="pending",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    # Tenant A can see their slot
    resp_a = await tenant_admin_client.get(SLOTS_URL)
    assert resp_a.status_code == 200
    assert resp_a.json()["total"] >= 1

    # Tenant B cannot see tenant A's slots
    resp_b = await second_tenant_admin_client.get(SLOTS_URL)
    assert resp_b.status_code == 200
    ids_b = [s["id"] for s in resp_b.json()["items"]]
    assert str(slot.id) not in ids_b


@pytest.mark.asyncio
async def test_tenant_isolation_slot_detail(
    tenant_admin_client: AsyncClient,
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="private slot",
        status="pending",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    # Tenant B tries to access tenant A's slot directly
    resp = await second_tenant_admin_client.get(f"{SLOTS_URL}/{slot.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_notes(
    tenant_admin_client: AsyncClient,
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_tenant_admin,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="note slot",
        status="completed",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()
    note = Note(
        tenant_id=test_tenant.id,
        user_id=test_tenant_admin.id,
        slot_id=slot.id,
        content="Tenant A private note",
    )
    db_session.add(note)
    await db_session.flush()

    # Tenant B cannot see tenant A's notes
    resp_b = await second_tenant_admin_client.get(NOTES_URL)
    assert resp_b.status_code == 200
    ids_b = [n["id"] for n in resp_b.json()["items"]]
    assert str(note.id) not in ids_b


@pytest.mark.asyncio
async def test_tenant_isolation_evaluations(
    tenant_admin_client: AsyncClient,
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="eval slot",
        status="completed",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    evaluation = Evaluation(
        slot_id=slot.id,
        tenant_id=test_tenant.id,
        ai_provider="openai",
        ai_model="gpt-4o",
        score_overall=90.0,
        score_sentiment=85.0,
        score_politeness=88.0,
        score_compliance=92.0,
        score_resolution=80.0,
        score_upselling=70.0,
        score_response_time=75.0,
        score_honesty=95.0,
        sentiment_label="positive",
        language_detected="en",
        summary="Good",
        strengths=[],
        weaknesses=[],
        recommendations=[],
        unclear_items=[],
        flags=[],
        tokens_used=100,
        evaluation_duration_ms=500,
        is_unclear=False,
    )
    db_session.add(evaluation)
    await db_session.flush()

    # Tenant B tries to read tenant A's evaluation
    resp = await second_tenant_admin_client.get(f"{EVALUATIONS_URL}/{slot.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_terminals(
    tenant_admin_client: AsyncClient,
    second_tenant_admin_client: AsyncClient,
    test_terminal,
    second_terminal,
):
    # Tenant A can see their terminal
    resp_a = await tenant_admin_client.get(TERMINALS_URL)
    assert resp_a.status_code == 200
    ids_a = [t["id"] for t in resp_a.json()["items"]]
    assert str(test_terminal.id) in ids_a

    # Tenant B cannot see tenant A's terminals
    resp_b = await second_tenant_admin_client.get(TERMINALS_URL)
    assert resp_b.status_code == 200
    ids_b = [t["id"] for t in resp_b.json()["items"]]
    assert str(test_terminal.id) not in ids_b


# --- JWT Edge Cases ---


@pytest.mark.asyncio
async def test_expired_jwt_rejected(client: AsyncClient, test_tenant_admin):
    from app.core.config import settings
    from jose import jwt

    payload = {
        "sub": str(test_tenant_admin.id),
        "role": "tenant_admin",
        "tenant_id": str(test_tenant_admin.tenant_id),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "type": "access",
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_malformed_jwt_rejected(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.real.jwt"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_missing_authorization_header(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_bearer_with_wrong_token_type(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code in (401, 403)


# --- API Key Edge Cases ---


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client: AsyncClient):
    now = datetime.now(UTC)
    payload = {
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=5)).isoformat(),
        "raw_text": "test",
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers={"Authorization": "Bearer totally_invalid_api_key_here"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_revoked_terminal_api_key_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    create_terminal,
    create_tenant,
    create_plan,
    terminal_headers,
):
    plan = await create_plan()
    tenant = await create_tenant(plan_id=plan.id)
    terminal = await create_terminal(tenant_id=tenant.id, status="revoked")

    now = datetime.now(UTC)
    payload = {
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=5)).isoformat(),
        "raw_text": "test with revoked terminal",
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers=terminal_headers(terminal),
    )
    assert response.status_code in (401, 403)
