"""Tests for RBAC privilege escalation prevention and new features."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.slot import Slot

USERS_URL = "/api/v1/users"
TERMINALS_URL = "/api/v1/terminals"
DASHBOARD_URL = "/api/v1/dashboard/stats"
SLOTS_URL = "/api/v1/slots"


# --- Privilege Escalation Prevention ---


@pytest.mark.asyncio
async def test_manager_cannot_invite_admin(
    manager_client: AsyncClient,
    test_tenant,
):
    response = await manager_client.post(
        f"{USERS_URL}/invite",
        json={
            "email": "escalation@example.com",
            "full_name": "Escalation User",
            "role": "tenant_admin",
        },
    )
    assert response.status_code == 403
    assert "above your own role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_manager_cannot_invite_super_admin(
    manager_client: AsyncClient,
    test_tenant,
):
    response = await manager_client.post(
        f"{USERS_URL}/invite",
        json={
            "email": "escalation2@example.com",
            "full_name": "Escalation User",
            "role": "super_admin",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_manager_can_invite_viewer(
    manager_client: AsyncClient,
    test_tenant,
    db_session: AsyncSession,
):
    response = await manager_client.post(
        f"{USERS_URL}/invite",
        json={
            "email": "viewer-ok@example.com",
            "full_name": "OK Viewer",
            "role": "viewer",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_manager_cannot_promote_user_to_admin(
    manager_client: AsyncClient,
    test_tenant,
    db_session: AsyncSession,
    create_user,
):
    target = await create_user(tenant_id=test_tenant.id, role="viewer", email="target-promote@example.com")
    response = await manager_client.patch(
        f"{USERS_URL}/{target.id}",
        json={"role": "tenant_admin"},
    )
    assert response.status_code == 403
    assert "above your own level" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tenant_admin_cannot_promote_to_super_admin(
    tenant_admin_client: AsyncClient,
    test_tenant,
    db_session: AsyncSession,
    create_user,
):
    target = await create_user(tenant_id=test_tenant.id, role="viewer", email="target-super@example.com")
    response = await tenant_admin_client.patch(
        f"{USERS_URL}/{target.id}",
        json={"role": "super_admin"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tenant_admin_can_promote_viewer_to_manager(
    tenant_admin_client: AsyncClient,
    test_tenant,
    db_session: AsyncSession,
    create_user,
):
    target = await create_user(tenant_id=test_tenant.id, role="viewer", email="target-manager@example.com")
    response = await tenant_admin_client.patch(
        f"{USERS_URL}/{target.id}",
        json={"role": "manager"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_self_deletion_blocked(
    tenant_admin_client: AsyncClient,
    test_tenant_admin,
):
    response = await tenant_admin_client.delete(f"{USERS_URL}/{test_tenant_admin.id}")
    assert response.status_code == 400
    assert "own account" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_delete_other_user(
    tenant_admin_client: AsyncClient,
    test_tenant,
    db_session: AsyncSession,
    create_user,
):
    target = await create_user(tenant_id=test_tenant.id, role="viewer", email="delete-target@example.com")
    response = await tenant_admin_client.delete(f"{USERS_URL}/{target.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_invalid_role_rejected_in_invite(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(
        f"{USERS_URL}/invite",
        json={
            "email": "badrole@example.com",
            "full_name": "Bad Role",
            "role": "god_mode",
        },
    )
    assert response.status_code == 422


# --- Dashboard Stats ---


@pytest.mark.asyncio
async def test_dashboard_stats_success(
    tenant_admin_client: AsyncClient,
    test_tenant,
    test_terminal,
    db_session: AsyncSession,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="dashboard test",
        status="evaluated",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await tenant_admin_client.get(DASHBOARD_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "slots_today" in data["data"]
    assert "active_terminals" in data["data"]
    assert "avg_score_week" in data["data"]


@pytest.mark.asyncio
async def test_dashboard_stats_viewer_allowed(
    viewer_client: AsyncClient,
):
    response = await viewer_client.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_stats_unauthenticated(client: AsyncClient):
    response = await client.get(DASHBOARD_URL)
    assert response.status_code in (401, 403)


# --- Terminal Ping ---


@pytest.mark.asyncio
async def test_terminal_ping_success(
    tenant_admin_client: AsyncClient,
    test_terminal,
):
    response = await tenant_admin_client.post(f"{TERMINALS_URL}/{test_terminal.id}/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["terminal_id"] == str(test_terminal.id)
    assert data["data"]["last_seen_at"] is not None


@pytest.mark.asyncio
async def test_terminal_ping_not_found(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(f"{TERMINALS_URL}/{uuid4()}/ping")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_terminal_ping_viewer_forbidden(
    viewer_client: AsyncClient,
    test_terminal,
):
    response = await viewer_client.post(f"{TERMINALS_URL}/{test_terminal.id}/ping")
    assert response.status_code == 403


# --- Bulk Re-evaluate ---


@pytest.mark.asyncio
async def test_bulk_re_evaluate_success(
    tenant_admin_client: AsyncClient,
    test_tenant,
    test_terminal,
    db_session: AsyncSession,
):
    slots = []
    for i in range(3):
        s = Slot(
            tenant_id=test_tenant.id,
            terminal_id=test_terminal.id,
            started_at=datetime.now(UTC) - timedelta(minutes=5 + i),
            ended_at=datetime.now(UTC) - timedelta(minutes=i),
            raw_text=f"bulk slot {i}",
            status="evaluated",
            metadata_={},
        )
        db_session.add(s)
        slots.append(s)
    await db_session.flush()

    slot_ids = [str(s.id) for s in slots]
    response = await tenant_admin_client.post(
        f"{SLOTS_URL}/bulk-re-evaluate",
        json={"slot_ids": slot_ids},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["queued"] == 3
    assert len(data["slot_ids"]) == 3


@pytest.mark.asyncio
async def test_bulk_re_evaluate_viewer_forbidden(
    viewer_client: AsyncClient,
):
    response = await viewer_client.post(
        f"{SLOTS_URL}/bulk-re-evaluate",
        json={"slot_ids": [str(uuid4())]},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_re_evaluate_empty_ids(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(
        f"{SLOTS_URL}/bulk-re-evaluate",
        json={"slot_ids": []},
    )
    assert response.status_code == 400


# --- Slot Score Filters ---


@pytest.mark.asyncio
async def test_list_slots_with_score_filter(
    tenant_admin_client: AsyncClient,
    test_tenant,
    test_terminal,
    db_session: AsyncSession,
):
    from uuid import UUID

    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=datetime.now(UTC),
        raw_text="score filter slot",
        status="evaluated",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    evaluation = Evaluation(
        slot_id=slot.id,
        tenant_id=test_tenant.id,
        ai_provider="openai",
        ai_model="gpt-4o",
        score_overall=85.0,
        raw_response={},
        is_unclear=False,
    )
    db_session.add(evaluation)
    await db_session.flush()

    response = await tenant_admin_client.get(f"{SLOTS_URL}?min_score=80&max_score=90")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()["items"]]
    assert str(slot.id) in ids

    response_excluded = await tenant_admin_client.get(f"{SLOTS_URL}?min_score=90")
    assert response_excluded.status_code == 200
    ids_excluded = [s["id"] for s in response_excluded.json()["items"]]
    assert str(slot.id) not in ids_excluded


# --- Input Validation: Invalid Dates ---


@pytest.mark.asyncio
async def test_list_slots_invalid_date_from(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get(f"{SLOTS_URL}?date_from=not-a-date")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_aggregations_invalid_period_start(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get("/api/v1/aggregations?period_start=invalid")
    assert response.status_code == 400
