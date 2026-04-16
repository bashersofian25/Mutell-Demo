from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportDownloadResponse,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = ReportService(db)
    return await svc.list_reports(tenant_id=str(user.tenant_id), page=page, per_page=per_page)


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ReportResponse)
async def create_report(
    body: ReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "viewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot generate reports")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = ReportService(db)
    return await svc.create_report(tenant_id=str(user.tenant_id), user_id=str(user.id), body=body)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = ReportService(db)
    report = await svc.get_report(tenant_id=str(user.tenant_id), report_id=str(report_id))
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("/{report_id}/download", response_model=ReportDownloadResponse)
async def download_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = ReportService(db)
    url = await svc.get_download_url(tenant_id=str(user.tenant_id), report_id=str(report_id))
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found or not ready")
    return ReportDownloadResponse(download_url=url)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("super_admin", "tenant_admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no tenant")

    svc = ReportService(db)
    success = await svc.delete_report(tenant_id=str(user.tenant_id), report_id=str(report_id))
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
