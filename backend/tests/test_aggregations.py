from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregated_evaluation import AggregatedEvaluation

AGGREGATIONS_URL = "/api/v1/aggregations"


@pytest.mark.asyncio
async def test_list_aggregations_empty(tenant_admin_client: AsyncClient):
    response = await tenant_admin_client.get(
        AGGREGATIONS_URL,
        params={
            "period_type": "day",
            "period_start": "2025-01-15T00:00:00Z",
            "period_end": "2025-01-15T23:59:59Z",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_aggregations_with_data(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    agg = AggregatedEvaluation(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        period_type="day",
        period_start=datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc),
        period_end=datetime(2025, 1, 15, 23, 59, 59, tzinfo=timezone.utc),
        slot_count=10,
        avg_overall=82.5,
        avg_sentiment=85.0,
        avg_politeness=88.0,
        avg_compliance=90.0,
        avg_resolution=78.0,
        avg_upselling=70.0,
        avg_response_time=75.0,
        avg_honesty=88.0,
        unclear_count=1,
        flag_counts={"rude": 1, "slow": 2},
    )
    db_session.add(agg)
    await db_session.flush()

    response = await tenant_admin_client.get(
        AGGREGATIONS_URL,
        params={
            "period_type": "day",
            "period_start": "2025-01-15T00:00:00Z",
            "period_end": "2025-01-15T23:59:59Z",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["slot_count"] == 10 for item in data["items"])
    matched = next(item for item in data["items"] if item["slot_count"] == 10)
    assert matched["avg_overall"] == 82.5
    assert matched["period_type"] == "day"
    assert matched["flag_counts"] == {"rude": 1, "slow": 2}


@pytest.mark.asyncio
async def test_aggregations_terminal_id_filter(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
    create_terminal,
):
    other_terminal = await create_terminal(tenant_id=test_tenant.id)
    agg_a = AggregatedEvaluation(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        period_type="day",
        period_start=datetime(2025, 3, 10, 0, 0, tzinfo=timezone.utc),
        period_end=datetime(2025, 3, 10, 23, 59, 59, tzinfo=timezone.utc),
        slot_count=5,
        avg_overall=80.0,
        avg_sentiment=82.0,
        avg_politeness=84.0,
        avg_compliance=86.0,
        avg_resolution=88.0,
        avg_upselling=70.0,
        avg_response_time=75.0,
        avg_honesty=90.0,
        unclear_count=0,
        flag_counts={},
    )
    agg_b = AggregatedEvaluation(
        tenant_id=test_tenant.id,
        terminal_id=other_terminal.id,
        period_type="day",
        period_start=datetime(2025, 3, 11, 0, 0, tzinfo=timezone.utc),
        period_end=datetime(2025, 3, 11, 23, 59, 59, tzinfo=timezone.utc),
        slot_count=15,
        avg_overall=90.0,
        avg_sentiment=92.0,
        avg_politeness=94.0,
        avg_compliance=96.0,
        avg_resolution=98.0,
        avg_upselling=80.0,
        avg_response_time=85.0,
        avg_honesty=95.0,
        unclear_count=0,
        flag_counts={},
    )
    db_session.add_all([agg_a, agg_b])
    await db_session.flush()

    response = await tenant_admin_client.get(
        AGGREGATIONS_URL,
        params={
            "period_type": "day",
            "period_start": "2025-03-10T00:00:00Z",
            "period_end": "2025-03-11T23:59:59Z",
            "terminal_id": str(test_terminal.id),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["terminal_id"] == str(test_terminal.id) for item in data["items"])


@pytest.mark.asyncio
async def test_aggregations_cross_tenant_isolation(
    second_tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_terminal,
):
    agg = AggregatedEvaluation(
        tenant_id=test_tenant.id,
        terminal_id=test_terminal.id,
        period_type="day",
        period_start=datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc),
        period_end=datetime(2025, 1, 15, 23, 59, 59, tzinfo=timezone.utc),
        slot_count=10,
        avg_overall=82.5,
        avg_sentiment=85.0,
        avg_politeness=88.0,
        avg_compliance=90.0,
        avg_resolution=78.0,
        avg_upselling=70.0,
        avg_response_time=75.0,
        avg_honesty=88.0,
        unclear_count=0,
        flag_counts={},
    )
    db_session.add(agg)
    await db_session.flush()

    response = await second_tenant_admin_client.get(
        AGGREGATIONS_URL,
        params={
            "period_type": "day",
            "period_start": "2025-01-15T00:00:00Z",
            "period_end": "2025-01-15T23:59:59Z",
        },
    )
    assert response.status_code == 200
    data = response.json()
    ids = [item.get("terminal_id") for item in data["items"]]
    assert str(test_terminal.id) not in ids


@pytest.mark.asyncio
async def test_aggregations_unauthenticated(client: AsyncClient):
    response = await client.get(
        AGGREGATIONS_URL,
        params={"period_type": "day"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_aggregations_invalid_terminal_id(tenant_admin_client: AsyncClient):
    response = await tenant_admin_client.get(
        AGGREGATIONS_URL,
        params={
            "period_type": "day",
            "terminal_id": "not-a-uuid",
        },
    )
    assert response.status_code == 422
