import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_tenant_admin: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_tenant_admin.email,
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_tenant_admin.email


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_tenant_admin: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_tenant_admin.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_email_format(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "testpass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_inactive_user(
    client: AsyncClient,
    create_user,
    test_tenant,
):
    user = await create_user(tenant_id=test_tenant.id, role="viewer", status="inactive")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "testpass123"},
    )
    # The login itself may succeed or fail depending on implementation,
    # but using the resulting token should fail at get_current_user
    if response.status_code == 200:
        token = response.json()["access_token"]
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 403
    else:
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_tenant_admin: User):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_tenant_admin.email,
            "password": "testpass123",
        },
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.refresh.token"},
    )
    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_missing(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_logout_success(tenant_admin_client: AsyncClient):
    response = await tenant_admin_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


@pytest.mark.asyncio
async def test_logout_unauthenticated(client: AsyncClient):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_success(viewer_client: AsyncClient, test_viewer_user: User):
    response = await viewer_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_viewer_user.email
    assert data["role"] == "viewer"
    assert "id" in data
    assert "full_name" in data


@pytest.mark.asyncio
async def test_get_me_response_structure(viewer_client: AsyncClient, test_viewer_user: User):
    response = await viewer_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    for field in ("id", "email", "full_name", "role", "tenant_id"):
        assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient, test_viewer_user: User):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_viewer_user.email},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_forgot_password_no_information_leakage(client: AsyncClient, test_viewer_user: User):
    resp_existing = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_viewer_user.email},
    )
    resp_nonexistent = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    # Both must return same status and structure
    assert resp_existing.status_code == resp_nonexistent.status_code
    assert resp_existing.json() == resp_nonexistent.json()


@pytest.mark.asyncio
async def test_forgot_password_invalid_email(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "not-an-email"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_success(
    client: AsyncClient,
    test_tenant_admin: User,
    auth_headers,
):
    headers = auth_headers(test_tenant_admin)
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "testpass123",
            "new_password": "newpass456",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_tenant_admin.email,
            "password": "newpass456",
        },
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(
    client: AsyncClient,
    test_tenant_admin: User,
    auth_headers,
):
    headers = auth_headers(test_tenant_admin)
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpass456",
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_missing_fields(
    client: AsyncClient,
    test_tenant_admin: User,
    auth_headers,
):
    headers = auth_headers(test_tenant_admin)
    response = await client.post(
        "/api/v1/auth/change-password",
        json={},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_unauthenticated(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "x", "new_password": "y"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid-reset-token",
            "new_password": "newpass456",
        },
    )
    assert response.status_code == 400
    assert "Invalid or expired reset token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_missing_fields(client: AsyncClient):
    response = await client.post("/api/v1/auth/reset-password", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/accept-invite",
        json={
            "token": "invalid-invite-token",
            "full_name": "New User",
            "password": "newpass456",
        },
    )
    assert response.status_code == 400
    assert "Invalid or expired invitation" in response.json()["detail"]


@pytest.mark.asyncio
async def test_accept_invite_missing_fields(client: AsyncClient):
    response = await client.post("/api/v1/auth/accept-invite", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_accept_invite_success(
    client: AsyncClient,
    create_user,
    test_tenant,
):
    from datetime import UTC, datetime, timedelta

    invite_token = "valid-invite-token-123"
    user = await create_user(
        tenant_id=test_tenant.id,
        role="viewer",
        status="invited",
        invite_token=invite_token,
        invite_expires=datetime.now(UTC) + timedelta(days=1),
        email="invited@example.com",
        password_hash=None,
    )

    response = await client.post(
        "/api/v1/auth/accept-invite",
        json={
            "token": invite_token,
            "full_name": "Accepted User",
            "password": "mynewpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "invited@example.com"


@pytest.mark.asyncio
async def test_accept_invite_expired_token(
    client: AsyncClient,
    create_user,
    test_tenant,
):
    from datetime import UTC, datetime, timedelta

    expired_token = "expired-invite-token-456"
    user = await create_user(
        tenant_id=test_tenant.id,
        role="viewer",
        status="invited",
        invite_token=expired_token,
        invite_expires=datetime.now(UTC) - timedelta(days=1),
        email="expired@example.com",
    )

    response = await client.post(
        "/api/v1/auth/accept-invite",
        json={
            "token": expired_token,
            "full_name": "Expired User",
            "password": "somepassword",
        },
    )
    assert response.status_code == 400
