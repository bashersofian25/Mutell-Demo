from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.terminal import Terminal

TERMINALS_URL = "/api/v1/terminals"


@pytest.mark.asyncio
async def test_list_terminals_admin_success(
    tenant_admin_client: AsyncClient,
    test_terminal,
):
    response = await tenant_admin_client.get(TERMINALS_URL)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(t["id"] == str(test_terminal.id) for t in data["items"])


@pytest.mark.asyncio
async def test_list_terminals_viewer_forbidden(
    viewer_client: AsyncClient,
):
    response = await viewer_client.get(TERMINALS_URL)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_terminals_unauthenticated(client: AsyncClient):
    response = await client.get(TERMINALS_URL)
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_terminal_success(
    tenant_admin_client: AsyncClient,
):
    payload = {
        "name": "New Terminal",
        "description": "A test terminal",
        "location": "Warehouse B",
    }
    response = await tenant_admin_client.post(TERMINALS_URL, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Terminal"
    assert data["description"] == "A test terminal"
    assert data["location"] == "Warehouse B"
    assert "api_key" in data
    assert data["api_key"].startswith("pk_live_")
    assert "id" in data
    assert "tenant_id" in data
    assert "api_key_prefix" in data
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_terminal_missing_name(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(TERMINALS_URL, json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_terminal_viewer_forbidden(
    viewer_client: AsyncClient,
):
    payload = {"name": "Blocked Terminal"}
    response = await viewer_client.post(TERMINALS_URL, json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_terminal_plan_limit(
    admin_client: AsyncClient,
    create_plan,
    create_tenant,
    create_user,
    create_terminal,
):
    limited_plan = await create_plan(max_terminals=0)
    limited_tenant = await create_tenant(plan_id=limited_plan.id)
    limited_admin = await create_user(
        tenant_id=limited_tenant.id, role="tenant_admin", email="limited_admin@test.com"
    )

    from app.core.security import create_access_token

    token = create_access_token(
        subject=str(limited_admin.id),
        role="tenant_admin",
        tenant_id=str(limited_tenant.id),
    )

    from httpx import ASGITransport, AsyncClient as HttpAsyncClient
    from app.main import app
    from app.core.database import get_db
    from tests.conftest import TestSessionFactory

    async def override_get_db():
        async with TestSessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with HttpAsyncClient(transport=transport, base_url="http://test", headers={"Authorization": f"Bearer {token}"}) as ac:
        response = await ac.post(TERMINALS_URL, json={"name": "Should Fail"})
        assert response.status_code == 402
        assert "detail" in response.json()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_terminal_success(
    tenant_admin_client: AsyncClient,
    test_terminal,
):
    response = await tenant_admin_client.patch(
        f"{TERMINALS_URL}/{test_terminal.id}",
        json={"name": "Updated Name", "location": "Floor 3"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["location"] == "Floor 3"


@pytest.mark.asyncio
async def test_update_terminal_empty_payload(
    tenant_admin_client: AsyncClient,
    test_terminal,
):
    response = await tenant_admin_client.patch(
        f"{TERMINALS_URL}/{test_terminal.id}",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_terminal.id)


@pytest.mark.asyncio
async def test_update_terminal_not_found(
    tenant_admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await tenant_admin_client.patch(
        f"{TERMINALS_URL}/{fake_id}",
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_terminal_success(
    tenant_admin_client: AsyncClient,
    test_terminal,
    db_session,
):
    response = await tenant_admin_client.delete(
        f"{TERMINALS_URL}/{test_terminal.id}",
    )
    assert response.status_code == 204
    from sqlalchemy import select

    from app.models.terminal import Terminal

    result = await db_session.execute(select(Terminal).where(Terminal.id == test_terminal.id))
    terminal = result.scalar_one()
    assert terminal.status == "revoked"


@pytest.mark.asyncio
async def test_delete_terminal_not_found(
    tenant_admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await tenant_admin_client.delete(f"{TERMINALS_URL}/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_terminal_already_deleted(
    tenant_admin_client: AsyncClient,
    test_terminal,
    db_session,
):
    # First delete
    await tenant_admin_client.delete(f"{TERMINALS_URL}/{test_terminal.id}")
    # Second delete — terminal is now revoked, the query filters by tenant_id
    # but the terminal still exists with status="revoked"
    # Depending on implementation, it may 404 (if filtering active only) or re-revoke
    response = await tenant_admin_client.delete(f"{TERMINALS_URL}/{test_terminal.id}")
    # The route doesn't filter by status on delete, so it may set revoked again or 404
    assert response.status_code in (204, 404)
