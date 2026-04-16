from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report

REPORTS_URL = "/api/v1/reports"


@pytest.mark.asyncio
async def test_list_reports_empty(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.get(REPORTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_reports_with_data(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_tenant_admin,
):
    now = datetime.now(UTC)
    report = Report(
        tenant_id=test_tenant.id,
        generated_by=test_tenant_admin.id,
        title="Test Report",
        period_start=now - timedelta(days=7),
        period_end=now,
        status="pending",
        file_url="",
    )
    db_session.add(report)
    await db_session.flush()

    response = await tenant_admin_client.get(REPORTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(r["title"] == "Test Report" for r in data["items"])


@pytest.mark.asyncio
async def test_create_report_success(
    tenant_admin_client: AsyncClient,
):
    now = datetime.now(UTC)
    payload = {
        "title": "Monthly Report",
        "period_start": now.isoformat(),
        "period_end": (now + timedelta(days=30)).isoformat(),
    }
    response = await tenant_admin_client.post(REPORTS_URL, json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["title"] == "Monthly Report"
    assert data["status"] in ("pending", "processing", "generating")
    assert "tenant_id" in data


@pytest.mark.asyncio
async def test_create_report_missing_fields(
    tenant_admin_client: AsyncClient,
):
    response = await tenant_admin_client.post(REPORTS_URL, json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_report_viewer_forbidden(
    viewer_client: AsyncClient,
):
    now = datetime.now(UTC)
    payload = {
        "title": "Monthly Report",
        "period_start": now.isoformat(),
        "period_end": (now + timedelta(days=30)).isoformat(),
    }
    response = await viewer_client.post(REPORTS_URL, json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_download_report_not_found(
    tenant_admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await tenant_admin_client.get(f"{REPORTS_URL}/{fake_id}/download")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_report_success(
    tenant_admin_client: AsyncClient,
    db_session: AsyncSession,
    test_tenant,
    test_tenant_admin,
):
    report = Report(
        tenant_id=test_tenant.id,
        generated_by=test_tenant_admin.id,
        title="Deletable Report",
        period_start=datetime.now(UTC) - timedelta(days=1),
        period_end=datetime.now(UTC),
        status="pending",
        file_url="",
    )
    db_session.add(report)
    await db_session.flush()

    response = await tenant_admin_client.delete(f"{REPORTS_URL}/{report.id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_report_not_found(
    tenant_admin_client: AsyncClient,
):
    fake_id = uuid4()
    response = await tenant_admin_client.delete(f"{REPORTS_URL}/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_report_viewer_forbidden(
    viewer_client: AsyncClient,
):
    fake_id = uuid4()
    response = await viewer_client.delete(f"{REPORTS_URL}/{fake_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_reports_unauthenticated(client: AsyncClient):
    response = await client.get(REPORTS_URL)
    assert response.status_code in (401, 403)
