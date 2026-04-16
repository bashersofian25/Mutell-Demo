from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.ai_provider import AIProvider

AI_CONFIGS_URL = "/api/v1/settings/ai"


@pytest.mark.asyncio
async def test_list_ai_configs_empty(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    response = await tenant_admin_client.get(AI_CONFIGS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_ai_config_success(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    response = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-123",
            "is_default": True,
            "custom_prompt": "Be helpful",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider_id"] == str(test_ai_provider.id)
    assert data["provider_slug"] == "openai"
    assert data["provider_name"] == "OpenAI"
    assert data["model_id"] == "gpt-4"
    assert data["is_default"] is True
    assert data["custom_prompt"] == "Be helpful"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_ai_config_missing_api_key(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    response = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_ai_config_viewer_forbidden(
    viewer_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    response = await viewer_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-123",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_ai_config_invalid_provider(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(uuid4()),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-123",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_multiple_defaults(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    # Create first default
    resp1 = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-1",
            "is_default": True,
        },
    )
    assert resp1.status_code == 201
    first_id = resp1.json()["id"]

    # Create second default — should unset the first
    resp2 = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4o",
            "api_key": "sk-test-key-2",
            "is_default": True,
        },
    )
    assert resp2.status_code == 201
    second_id = resp2.json()["id"]

    # List and verify only one is default
    list_resp = await tenant_admin_client.get(AI_CONFIGS_URL)
    assert list_resp.status_code == 200
    configs = list_resp.json()["items"]
    defaults = [c for c in configs if c["is_default"] is True]
    assert len(defaults) == 1
    assert defaults[0]["id"] == second_id


@pytest.mark.asyncio
async def test_update_ai_config_success(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    create_resp = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-123",
        },
    )
    assert create_resp.status_code == 201
    config_id = create_resp.json()["id"]

    response = await tenant_admin_client.patch(
        f"{AI_CONFIGS_URL}/{config_id}",
        json={
            "model_id": "gpt-4o",
            "is_default": True,
            "custom_prompt": "Updated prompt",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "gpt-4o"
    assert data["is_default"] is True
    assert data["custom_prompt"] == "Updated prompt"
    assert data["provider_slug"] == "openai"
    assert data["provider_name"] == "OpenAI"


@pytest.mark.asyncio
async def test_update_ai_config_not_found(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.patch(
        f"{AI_CONFIGS_URL}/{uuid4()}",
        json={"model_id": "gpt-4o"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_ai_config_viewer_forbidden(
    viewer_client: AsyncClient,
):
    response = await viewer_client.patch(
        f"{AI_CONFIGS_URL}/{uuid4()}",
        json={"model_id": "gpt-4o"},
    )
    assert response.status_code in (403, 404)


@pytest.mark.asyncio
async def test_delete_ai_config_success(
    tenant_admin_client: AsyncClient,
    test_ai_provider: AIProvider,
):
    create_resp = await tenant_admin_client.post(
        AI_CONFIGS_URL,
        json={
            "provider_id": str(test_ai_provider.id),
            "model_id": "gpt-4",
            "api_key": "sk-test-key-123",
        },
    )
    assert create_resp.status_code == 201
    config_id = create_resp.json()["id"]

    response = await tenant_admin_client.delete(f"{AI_CONFIGS_URL}/{config_id}")
    assert response.status_code == 204

    list_resp = await tenant_admin_client.get(AI_CONFIGS_URL)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_ai_config_not_found(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.delete(f"{AI_CONFIGS_URL}/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_ai_config_viewer_forbidden(
    viewer_client: AsyncClient,
):
    response = await viewer_client.delete(f"{AI_CONFIGS_URL}/{uuid4()}")
    assert response.status_code in (403, 404)


@pytest.mark.asyncio
async def test_list_ai_configs_no_tenant(
    admin_client: AsyncClient,
):
    response = await admin_client.get(AI_CONFIGS_URL)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_ai_configs_unauthenticated(client: AsyncClient):
    response = await client.get(AI_CONFIGS_URL)
    assert response.status_code in (401, 403)
