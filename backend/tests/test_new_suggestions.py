from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["role"] == "tenant_admin"
    assert data["user"]["tenant_id"] is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "full_name": "First",
            "password": "securepass123",
        },
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "full_name": "Second",
            "password": "securepass123",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_join_existing_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "joiner@example.com",
            "full_name": "Joiner",
            "password": "securepass123",
            "tenant_slug": test_tenant.slug,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "viewer"
    assert data["user"]["tenant_id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_register_invalid_tenant_slug(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "badslug@example.com",
            "full_name": "Bad Slug",
            "password": "securepass123",
            "tenant_slug": "nonexistent-slug-xyz",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@example.com",
            "full_name": "Short PW",
            "password": "abc",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_auth_invalid_token(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/auth/google",
        json={"id_token": "invalid-google-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_permissions_empty(
    tenant_admin_client: AsyncClient,
    test_viewer_user,
):
    response = await tenant_admin_client.get(
        f"/api/v1/users/{test_viewer_user.id}/permissions"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(test_viewer_user.id)
    assert isinstance(data["permissions"], list)


@pytest.mark.asyncio
async def test_get_permissions_after_set(
    tenant_admin_client: AsyncClient,
    test_viewer_user,
):
    await tenant_admin_client.put(
        f"/api/v1/users/{test_viewer_user.id}/permissions",
        json=[
            {"permission": "export_reports", "granted": True},
            {"permission": "view_analytics", "granted": False},
        ],
    )
    response = await tenant_admin_client.get(
        f"/api/v1/users/{test_viewer_user.id}/permissions"
    )
    assert response.status_code == 200
    data = response.json()
    perm_map = {p["permission"]: p["granted"] for p in data["permissions"]}
    assert perm_map["export_reports"] is True
    assert perm_map["view_analytics"] is False


@pytest.mark.asyncio
async def test_get_permissions_viewer_forbidden(
    viewer_client: AsyncClient,
    test_tenant_admin,
):
    response = await viewer_client.get(
        f"/api/v1/users/{test_tenant_admin.id}/permissions"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_permissions_not_found(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get(
        f"/api/v1/users/{uuid4()}/permissions"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_permission_schema(tenant_admin_client: AsyncClient):
    response = await tenant_admin_client.get("/api/v1/users/meta/permissions")
    assert response.status_code == 200
    data = response.json()
    assert "permissions" in data
    perms = data["permissions"]
    assert len(perms) >= 6
    assert all("key" in p and "label" in p and "description" in p for p in perms)
    keys = [p["key"] for p in perms]
    assert "export_reports" in keys
    assert "manage_terminals" in keys


@pytest.mark.asyncio
async def test_list_permission_schema_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/users/meta/permissions")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_report_success(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_tenant_admin,
):
    now = datetime.now(UTC)
    report = Report(
        tenant_id=test_tenant.id,
        generated_by=test_tenant_admin.id,
        title="Single Report",
        period_start=now - timedelta(days=7),
        period_end=now,
        status="pending",
        file_url="",
    )
    db_session.add(report)
    await db_session.flush()

    response = await tenant_admin_client.get(f"/api/v1/reports/{report.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(report.id)
    assert data["title"] == "Single Report"
    assert "status" in data


@pytest.mark.asyncio
async def test_get_report_not_found(tenant_admin_client: AsyncClient):
    response = await tenant_admin_client.get(f"/api/v1/reports/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_unauthenticated(client: AsyncClient):
    response = await client.get(f"/api/v1/reports/{uuid4()}")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_admin_update_provider_api_key(
    admin_client: AsyncClient,
    test_ai_provider,
):
    response = await admin_client.patch(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}",
        json={
            "api_key": "sk-super-secret-key-12345678",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["api_key"] is not None
    assert "sk-s" in data["data"]["api_key"]
    assert "5678" in data["data"]["api_key"]
    assert "secret" not in data["data"]["api_key"]


@pytest.mark.asyncio
async def test_admin_add_provider_model(
    admin_client: AsyncClient,
    test_ai_provider,
):
    response = await admin_client.post(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}/models",
        json={"model_id": "gpt-4-turbo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "gpt-4-turbo" in data["data"]["supported_models"]


@pytest.mark.asyncio
async def test_admin_add_duplicate_model(
    admin_client: AsyncClient,
    test_ai_provider,
):
    await admin_client.post(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}/models",
        json={"model_id": "gpt-4o"},
    )
    response = await admin_client.post(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}/models",
        json={"model_id": "gpt-4o"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["supported_models"].count("gpt-4o") == 1


@pytest.mark.asyncio
async def test_admin_remove_provider_model(
    admin_client: AsyncClient,
    test_ai_provider,
):
    await admin_client.post(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}/models",
        json={"model_id": "claude-3"},
    )
    response = await admin_client.delete(
        f"/api/v1/admin/ai-providers/{test_ai_provider.id}/models/claude-3",
    )
    assert response.status_code == 200
    data = response.json()
    assert "claude-3" not in data["data"]["supported_models"]


@pytest.mark.asyncio
async def test_admin_model_management_provider_not_found(admin_client: AsyncClient):
    response = await admin_client.post(
        f"/api/v1/admin/ai-providers/{uuid4()}/models",
        json={"model_id": "gpt-4"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_notification_settings_defaults(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get("/api/v1/settings/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["email_evaluations"] is True
    assert data["email_failures"] is True
    assert data["email_reports"] is False
    assert data["push_mentions"] is True
    assert data["push_weekly_summary"] is False


@pytest.mark.asyncio
async def test_update_notification_settings(
    tenant_admin_client: AsyncClient,
):
    await tenant_admin_client.get("/api/v1/settings/notifications")
    response = await tenant_admin_client.put(
        "/api/v1/settings/notifications",
        json={
            "email_evaluations": False,
            "email_failures": False,
            "email_reports": True,
            "push_mentions": False,
            "push_weekly_summary": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email_evaluations"] is False
    assert data["email_reports"] is True
    assert data["push_weekly_summary"] is True


@pytest.mark.asyncio
async def test_notification_settings_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/settings/notifications")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_dashboard_trends(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get("/api/v1/dashboard/trends")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_dashboard_trends_with_days(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get(
        "/api/v1/dashboard/trends", params={"days": 7}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_trends_no_tenant(
    admin_client: AsyncClient,
):
    response = await admin_client.get("/api/v1/dashboard/trends")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_audit_log_standard_format(
    admin_client: AsyncClient,
):
    response = await admin_client.get("/api/v1/admin/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert data["page"] == 1
    assert data["per_page"] == 50
