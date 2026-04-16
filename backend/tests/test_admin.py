from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.plan import Plan
from app.models.tenant import Tenant
from app.models.ai_provider import AIProvider

ADMIN_URL = "/api/v1/admin"

ADMIN_ENDPOINTS = [
    ("GET", "/tenants"),
    ("GET", "/plans"),
    ("GET", "/ai-providers"),
    ("GET", "/users"),
    ("GET", "/audit-log"),
    ("GET", "/health"),
]


@pytest.mark.asyncio
async def test_admin_list_tenants(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.get(f"{ADMIN_URL}/tenants")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(t["id"] == str(test_tenant.id) for t in data["items"])


@pytest.mark.asyncio
async def test_admin_create_tenant(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    payload = {
        "name": "New Tenant",
        "slug": f"new-tenant-{uuid4().hex[:8]}",
        "contact_email": "newtenant@example.com",
        "timezone": "UTC",
        "plan_id": str(test_plan.id),
    }
    response = await admin_client.post(f"{ADMIN_URL}/tenants", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Tenant"
    assert data["slug"] == payload["slug"]
    assert data["contact_email"] == "newtenant@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_admin_create_tenant_duplicate_slug(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    payload = {
        "name": "Duplicate Tenant",
        "slug": test_tenant.slug,
        "contact_email": "dup@example.com",
        "timezone": "UTC",
    }
    response = await admin_client.post(f"{ADMIN_URL}/tenants", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_admin_get_tenant(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.get(f"{ADMIN_URL}/tenants/{test_tenant.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_tenant.id)
    assert data["name"] == test_tenant.name
    assert data["slug"] == test_tenant.slug


@pytest.mark.asyncio
async def test_admin_get_tenant_not_found(
    admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await admin_client.get(f"{ADMIN_URL}/tenants/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_tenant(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.patch(
        f"{ADMIN_URL}/tenants/{test_tenant.id}",
        json={"name": "Updated Tenant"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Tenant"
    assert data["id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_admin_delete_tenant(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.delete(f"{ADMIN_URL}/tenants/{test_tenant.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_delete_tenant_not_found(
    admin_client: AsyncClient,
):
    response = await admin_client.delete(f"{ADMIN_URL}/tenants/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_list_plans(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await admin_client.get(f"{ADMIN_URL}/plans")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(p["id"] == str(test_plan.id) for p in data["items"])


@pytest.mark.asyncio
async def test_admin_create_plan(
    admin_client: AsyncClient,
):
    payload = {
        "name": "Admin Test Plan",
        "description": "Created via admin",
        "max_terminals": 10,
        "max_users": 20,
        "max_slots_per_day": 500,
        "retention_days": 30,
        "allowed_ai_providers": ["openai"],
        "custom_prompt_allowed": False,
        "report_export_allowed": True,
        "api_rate_limit_per_min": 100,
    }
    response = await admin_client.post(f"{ADMIN_URL}/plans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Admin Test Plan"
    assert data["max_terminals"] == 10
    assert "id" in data


@pytest.mark.asyncio
async def test_admin_update_plan(
    admin_client: AsyncClient,
    test_plan: Plan,
):
    response = await admin_client.patch(
        f"{ADMIN_URL}/plans/{test_plan.id}",
        json={"name": "Updated Admin Plan", "max_terminals": 99},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Admin Plan"
    assert data["max_terminals"] == 99


@pytest.mark.asyncio
async def test_admin_update_plan_not_found(
    admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await admin_client.patch(
        f"{ADMIN_URL}/plans/{fake_id}",
        json={"name": "Ghost Plan"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_list_ai_providers(
    admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    response = await admin_client.get(f"{ADMIN_URL}/ai-providers")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    assert any(p["id"] == str(test_ai_provider.id) for p in data["data"])
    provider_data = next(p for p in data["data"] if p["id"] == str(test_ai_provider.id))
    assert "slug" in provider_data
    assert "display_name" in provider_data
    assert "is_active" in provider_data
    assert "base_url" in provider_data
    assert "supported_models" in provider_data


@pytest.mark.asyncio
async def test_admin_toggle_ai_provider(
    admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    original_state = test_ai_provider.is_active
    response = await admin_client.patch(
        f"{ADMIN_URL}/ai-providers/{test_ai_provider.id}",
        json={"is_active": not original_state},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_active"] is (not original_state)
    assert data["data"]["id"] == str(test_ai_provider.id)
    assert data["data"]["slug"] == test_ai_provider.slug


@pytest.mark.asyncio
async def test_admin_toggle_ai_provider_not_found(
    admin_client: AsyncClient,
):
    response = await admin_client.patch(
        f"{ADMIN_URL}/ai-providers/{uuid4()}",
        json={"is_active": False},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_list_users(
    admin_client: AsyncClient,
):
    response = await admin_client.get(f"{ADMIN_URL}/users")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_audit_log(
    admin_client: AsyncClient,
):
    response = await admin_client.get(f"{ADMIN_URL}/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


@pytest.mark.asyncio
async def test_admin_audit_log_with_filters(
    admin_client: AsyncClient,
):
    response = await admin_client.get(
        f"{ADMIN_URL}/audit-log",
        params={
            "action": "login",
            "date_from": "2020-01-01T00:00:00",
            "date_to": "2030-12-31T23:59:59",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_admin_health(
    admin_client: AsyncClient,
):
    response = await admin_client.get(f"{ADMIN_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["database"] == "connected"
    assert data["data"]["redis"] in ("connected", "disconnected", "unknown")


@pytest.mark.asyncio
async def test_admin_non_admin_forbidden(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get(f"{ADMIN_URL}/tenants")
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
async def test_admin_all_endpoints_non_admin_forbidden(
    viewer_client: AsyncClient,
    method: str,
    path: str,
):
    response = await viewer_client.request(method, f"{ADMIN_URL}{path}")
    assert response.status_code == 403
