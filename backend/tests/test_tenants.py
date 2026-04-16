from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant

TENANTS_URL = "/api/v1/tenants"


@pytest.mark.asyncio
async def test_list_tenants_super_admin(
    admin_client: AsyncClient,
    test_tenant: Tenant,
    create_tenant,
):
    other = await create_tenant()
    response = await admin_client.get(TENANTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    ids = [t["id"] for t in data["items"]]
    assert str(test_tenant.id) in ids
    assert str(other.id) in ids


@pytest.mark.asyncio
async def test_list_tenants_tenant_admin(
    tenant_admin_client: AsyncClient,
    test_tenant: Tenant,
    test_tenant_admin,
):
    response = await tenant_admin_client.get(TENANTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_create_tenant_super_admin(
    admin_client: AsyncClient,
    test_plan,
):
    response = await admin_client.post(
        TENANTS_URL,
        json={
            "name": "New Tenant",
            "slug": "new-tenant",
            "contact_email": "new@example.com",
            "plan_id": str(test_plan.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Tenant"
    assert data["slug"] == "new-tenant"
    assert data["contact_email"] == "new@example.com"
    assert data["plan_id"] == str(test_plan.id)


@pytest.mark.asyncio
async def test_create_tenant_missing_required_fields(
    admin_client: AsyncClient,
):
    response = await admin_client.post(TENANTS_URL, json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_tenant_non_admin_forbidden(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(
        TENANTS_URL,
        json={
            "name": "Forbidden Tenant",
            "slug": "forbidden",
            "contact_email": "no@example.com",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.post(
        TENANTS_URL,
        json={
            "name": "Duplicate",
            "slug": test_tenant.slug,
            "contact_email": "dup@example.com",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_tenant_invalid_email(
    admin_client: AsyncClient,
):
    response = await admin_client.post(
        TENANTS_URL,
        json={
            "name": "Bad Email Tenant",
            "slug": "bad-email-tenant",
            "contact_email": "not-an-email",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_tenant_own(
    tenant_admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await tenant_admin_client.get(f"{TENANTS_URL}/{test_tenant.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_tenant.id)
    assert data["name"] == test_tenant.name


@pytest.mark.asyncio
async def test_get_tenant_other_forbidden(
    viewer_client: AsyncClient,
    create_tenant,
):
    other = await create_tenant()
    response = await viewer_client.get(f"{TENANTS_URL}/{other.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_tenant_not_found(
    admin_client: AsyncClient,
):
    from uuid import uuid4

    response = await admin_client.get(f"{TENANTS_URL}/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tenant_unauthenticated(client: AsyncClient):
    response = await client.get(f"{TENANTS_URL}/{uuid4()}")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_tenant_admin(
    admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await admin_client.patch(
        f"{TENANTS_URL}/{test_tenant.id}",
        json={"name": "Updated Name", "contact_email": "updated@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["contact_email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_tenant_tenant_admin_own(
    tenant_admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await tenant_admin_client.patch(
        f"{TENANTS_URL}/{test_tenant.id}",
        json={"name": "Tenant Admin Update", "timezone": "Europe/Berlin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tenant Admin Update"
    assert data["timezone"] == "Europe/Berlin"


@pytest.mark.asyncio
async def test_update_tenant_viewer_forbidden(
    viewer_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await viewer_client.patch(
        f"{TENANTS_URL}/{test_tenant.id}",
        json={"name": "Viewer Update"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_tenant_super_admin(
    admin_client: AsyncClient,
    create_tenant,
    db_session,
):
    tenant = await create_tenant()
    response = await admin_client.delete(f"{TENANTS_URL}/{tenant.id}")
    assert response.status_code == 204
    await db_session.flush()
    assert tenant.status == "deleted"


@pytest.mark.asyncio
async def test_delete_tenant_non_admin_forbidden(
    tenant_admin_client: AsyncClient,
    test_tenant: Tenant,
):
    response = await tenant_admin_client.delete(f"{TENANTS_URL}/{test_tenant.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_tenant_not_found(
    admin_client: AsyncClient,
):
    response = await admin_client.delete(f"{TENANTS_URL}/{uuid4()}")
    assert response.status_code == 404
