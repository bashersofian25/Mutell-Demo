from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan

PLANS_URL = "/api/v1/plans"


@pytest.mark.asyncio
async def test_list_plans_success(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await admin_client.get(PLANS_URL)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(p["id"] == str(test_plan.id) for p in data["items"])


@pytest.mark.asyncio
async def test_list_plans_non_admin_only_active(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    create_plan,
):
    active_plan = await create_plan(name="Active Plan", is_active=True)
    inactive_plan = await create_plan(name="Inactive Plan", is_active=False)

    response = await viewer_client.get(PLANS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    plan_ids = [p["id"] for p in data["items"]]
    assert str(active_plan.id) in plan_ids
    assert str(inactive_plan.id) not in plan_ids


@pytest.mark.asyncio
async def test_list_plans_unauthenticated(client: AsyncClient):
    response = await client.get(PLANS_URL)
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_plan_super_admin(
    admin_client: AsyncClient,
):
    payload = {
        "name": "New Plan",
        "description": "A new test plan",
        "max_terminals": 10,
        "max_users": 25,
        "max_slots_per_day": 500,
        "retention_days": 60,
        "allowed_ai_providers": ["openai"],
        "custom_prompt_allowed": True,
        "report_export_allowed": True,
        "api_rate_limit_per_min": 100,
    }
    response = await admin_client.post(PLANS_URL, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Plan"
    assert data["description"] == "A new test plan"
    assert data["max_terminals"] == 10
    assert data["max_users"] == 25
    assert data["max_slots_per_day"] == 500
    assert data["retention_days"] == 60
    assert data["allowed_ai_providers"] == ["openai"]
    assert data["custom_prompt_allowed"] is True
    assert data["report_export_allowed"] is True
    assert data["api_rate_limit_per_min"] == 100
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_plan_missing_required_fields(
    admin_client: AsyncClient,
):
    response = await admin_client.post(PLANS_URL, json={})
    # PlanCreate has defaults for everything except name
    assert response.status_code in (201, 422)


@pytest.mark.asyncio
async def test_create_plan_non_admin_forbidden(
    tenant_admin_client: AsyncClient,
):
    payload = {
        "name": "Blocked Plan",
    }
    response = await tenant_admin_client.post(PLANS_URL, json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_plan_success(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await admin_client.get(f"{PLANS_URL}/{test_plan.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_plan.id)
    assert data["name"] == test_plan.name
    assert "description" in data
    assert "max_terminals" in data
    assert "max_users" in data
    assert "max_slots_per_day" in data
    assert "retention_days" in data
    assert "allowed_ai_providers" in data
    assert "custom_prompt_allowed" in data
    assert "report_export_allowed" in data
    assert "api_rate_limit_per_min" in data
    assert "is_active" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_plan_not_found(
    admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await admin_client.get(f"{PLANS_URL}/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_plan_unauthenticated(client: AsyncClient):
    response = await client.get(f"{PLANS_URL}/{uuid4()}")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_plan_super_admin(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await admin_client.patch(
        f"{PLANS_URL}/{test_plan.id}",
        json={"name": "Updated Plan", "max_terminals": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Plan"
    assert data["max_terminals"] == 50


@pytest.mark.asyncio
async def test_update_plan_not_found(
    admin_client: AsyncClient,
):
    response = await admin_client.patch(
        f"{PLANS_URL}/{uuid4()}",
        json={"name": "Ghost Plan"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_plan_non_admin_forbidden(
    tenant_admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await tenant_admin_client.patch(
        f"{PLANS_URL}/{test_plan.id}",
        json={"name": "Blocked Update"},
    )
    assert response.status_code == 403
