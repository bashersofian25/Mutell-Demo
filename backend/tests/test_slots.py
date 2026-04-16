from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot import Slot

SLOTS_URL = "/api/v1/slots"

STT_RAW_TEXT = (
    "Merhaba, hoş geldiniz. Bugün size nasıl yardımcı olabilirim? "
    "Efendim, kredi başvurusu yapmak istiyorum. "
    "Tabii efendim, hemen size yardımcı oluyorum. "
    "Adınızı ve soyadınızı alabilir miyim? "
    "Mehmet Yılmaz. "
    "Teşekkür ederim Mehmet Bey. Başvurunuzu şu anda başlatabiliriz."
)


@pytest.mark.asyncio
async def test_create_slot_success(
    client: AsyncClient,
    db_session: AsyncSession,
    test_terminal,
    terminal_headers,
):
    now = datetime.now(UTC)
    payload = {
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=5)).isoformat(),
        "raw_text": STT_RAW_TEXT,
        "metadata": {"source": "stt", "language": "tr"},
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers=terminal_headers(test_terminal),
    )
    assert response.status_code == 202
    data = response.json()
    assert "slot_id" in data
    assert data["status"] == "accepted"
    assert "config" in data


@pytest.mark.asyncio
async def test_create_slot_unauthenticated(client: AsyncClient):
    now = datetime.now(UTC)
    payload = {
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=5)).isoformat(),
        "raw_text": "test",
    }
    response = await client.post(SLOTS_URL, json=payload)
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_slot_missing_required_fields(
    client: AsyncClient,
    test_terminal,
    terminal_headers,
):
    response = await client.post(
        SLOTS_URL,
        json={"raw_text": "test"},
        headers=terminal_headers(test_terminal),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_slot_invalid_datetime(
    client: AsyncClient,
    test_terminal,
    terminal_headers,
):
    payload = {
        "started_at": "not-a-date",
        "ended_at": "also-not-a-date",
        "raw_text": "test",
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers=terminal_headers(test_terminal),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_slot_with_revoked_terminal(
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
        "raw_text": "test with revoked",
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers=terminal_headers(terminal),
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_slot_plan_limit_exceeded(
    db_session: AsyncSession,
    create_plan,
    create_tenant,
    create_terminal,
    client: AsyncClient,
    terminal_headers,
):
    limited_plan = await create_plan(max_slots_per_day=0)
    limited_tenant = await create_tenant(plan_id=limited_plan.id)
    limited_terminal = await create_terminal(tenant_id=limited_tenant.id)

    now = datetime.now(UTC)
    payload = {
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=5)).isoformat(),
        "raw_text": "should be rejected",
    }
    response = await client.post(
        SLOTS_URL,
        json=payload,
        headers=terminal_headers(limited_terminal),
    )
    assert response.status_code == 402
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_list_slots_success(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=10),
        ended_at=datetime.now(UTC) - timedelta(minutes=5),
        raw_text="test listing",
        status="pending",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await tenant_admin_client.get(SLOTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_slots_with_filters(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot_pending = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(hours=2),
        ended_at=datetime.now(UTC) - timedelta(hours=1, minutes=55),
        raw_text="pending slot",
        status="pending",
        metadata_={},
    )
    slot_completed = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(hours=1),
        ended_at=datetime.now(UTC) - timedelta(minutes=55),
        raw_text="completed slot",
        status="completed",
        metadata_={},
    )
    db_session.add_all([slot_pending, slot_completed])
    await db_session.flush()

    response = await tenant_admin_client.get(
        SLOTS_URL,
        params={"status": "pending"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "pending" for item in data["items"])

    response = await tenant_admin_client.get(
        SLOTS_URL,
        params={"terminal_id": str(test_terminal.id)},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(
        item["terminal_id"] == str(test_terminal.id) for item in data["items"]
    )


@pytest.mark.asyncio
async def test_list_slots_date_range_filter(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    now = datetime.now(UTC)
    old_slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=now - timedelta(days=10),
        ended_at=now - timedelta(days=10, minutes=-5),
        raw_text="old slot",
        status="completed",
        metadata_={},
    )
    recent_slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=now - timedelta(hours=1),
        ended_at=now - timedelta(minutes=55),
        raw_text="recent slot",
        status="completed",
        metadata_={},
    )
    db_session.add_all([old_slot, recent_slot])
    await db_session.flush()

    yesterday = (now - timedelta(days=1)).isoformat()
    tomorrow = (now + timedelta(days=1)).isoformat()
    response = await tenant_admin_client.get(
        SLOTS_URL,
        params={"date_from": yesterday, "date_to": tomorrow},
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids = [s["id"] for s in data["items"]]
    assert str(recent_slot.id) in returned_ids
    assert str(old_slot.id) not in returned_ids


@pytest.mark.asyncio
async def test_list_slots_pagination(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    for i in range(5):
        slot = Slot(
            tenant_id=test_tenant.id,
            terminal_id=test_terminal.id,
            started_at=datetime.now(UTC) - timedelta(minutes=i + 1),
            ended_at=datetime.now(UTC) - timedelta(seconds=i * 30),
            raw_text=f"pagination slot {i}",
            status="pending",
            metadata_={},
        )
        db_session.add(slot)
    await db_session.flush()

    response = await tenant_admin_client.get(
        SLOTS_URL,
        params={"page": 1, "per_page": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["per_page"] == 2

    response2 = await tenant_admin_client.get(
        SLOTS_URL,
        params={"page": 2, "per_page": 2},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["page"] == 2


@pytest.mark.asyncio
async def test_get_slot_detail(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=10),
        ended_at=datetime.now(UTC) - timedelta(minutes=5),
        raw_text="detail view test raw text",
        status="pending",
        metadata_={"key": "value"},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await tenant_admin_client.get(f"{SLOTS_URL}/{slot.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(slot.id)
    assert data["raw_text"] == "detail view test raw text"
    assert data["status"] == "pending"
    assert data["evaluation"] is None


@pytest.mark.asyncio
async def test_get_slot_not_found(tenant_admin_client: AsyncClient):
    random_id = str(uuid4())
    response = await tenant_admin_client.get(f"{SLOTS_URL}/{random_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_slot_cross_tenant_forbidden(
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
        raw_text="private",
        status="pending",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await second_tenant_admin_client.get(f"{SLOTS_URL}/{slot.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_re_evaluate_slot_admin(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=10),
        ended_at=datetime.now(UTC) - timedelta(minutes=5),
        raw_text="re-evaluate test",
        status="completed",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await tenant_admin_client.post(f"{SLOTS_URL}/{slot.id}/re-evaluate")
    assert response.status_code == 200
    data = response.json()
    assert data["slot_id"] == str(slot.id)
    assert data["status"] == "re-evaluating"


@pytest.mark.asyncio
async def test_re_evaluate_slot_not_found(tenant_admin_client: AsyncClient):
    fake_id = str(uuid4())
    response = await tenant_admin_client.post(f"{SLOTS_URL}/{fake_id}/re-evaluate")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_re_evaluate_slot_viewer_forbidden(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    slot = Slot(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        started_at=datetime.now(UTC) - timedelta(minutes=10),
        ended_at=datetime.now(UTC) - timedelta(minutes=5),
        raw_text="viewer re-evaluate test",
        status="completed",
        metadata_={},
    )
    db_session.add(slot)
    await db_session.flush()

    response = await viewer_client.post(f"{SLOTS_URL}/{slot.id}/re-evaluate")
    assert response.status_code == 403
