from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.report import Report
from app.models.slot import Slot
from app.schemas.report import ReportCreate, ReportListResponse, ReportResponse


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self, tenant_id: str, user_id: str, body: ReportCreate
    ) -> ReportResponse:
        report = Report(
            tenant_id=UUID(tenant_id),
            generated_by=UUID(user_id),
            title=body.title,
            period_start=body.period_start,
            period_end=body.period_end,
            terminal_ids=[UUID(tid) for tid in body.terminal_ids] if body.terminal_ids else None,
            file_url="pending",
            status="generating",
        )
        self.db.add(report)
        await self.db.flush()

        try:
            from app.workers.report_worker import generate_report
            generate_report.delay(str(report.id))
        except Exception:
            pass

        return ReportResponse(
            id=str(report.id),
            tenant_id=str(report.tenant_id),
            generated_by=str(report.generated_by),
            title=report.title,
            period_start=report.period_start,
            period_end=report.period_end,
            terminal_ids=report.terminal_ids,
            file_url=report.file_url,
            file_size_bytes=report.file_size_bytes,
            status=report.status,
            created_at=report.created_at,
        )

    async def list_reports(self, tenant_id: str, page: int, per_page: int) -> ReportListResponse:
        query = select(Report).where(Report.tenant_id == UUID(tenant_id))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(Report.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        reports = result.scalars().all()

        return ReportListResponse(
            items=[
                ReportResponse(
                    id=str(r.id),
                    tenant_id=str(r.tenant_id),
                    generated_by=str(r.generated_by) if r.generated_by else None,
                    title=r.title,
                    period_start=r.period_start,
                    period_end=r.period_end,
                    terminal_ids=r.terminal_ids,
                    file_url=r.file_url,
                    file_size_bytes=r.file_size_bytes,
                    status=r.status,
                    created_at=r.created_at,
                )
                for r in reports
            ],
            total=total,
        )

    async def get_report(self, tenant_id: str, report_id: str) -> ReportResponse | None:
        result = await self.db.execute(
            select(Report).where(
                Report.id == UUID(report_id),
                Report.tenant_id == UUID(tenant_id),
            )
        )
        r = result.scalar_one_or_none()
        if r is None:
            return None

        return ReportResponse(
            id=str(r.id),
            tenant_id=str(r.tenant_id),
            generated_by=str(r.generated_by) if r.generated_by else None,
            title=r.title,
            period_start=r.period_start,
            period_end=r.period_end,
            terminal_ids=r.terminal_ids,
            file_url=r.file_url,
            file_size_bytes=r.file_size_bytes,
            status=r.status,
            created_at=r.created_at,
        )

    async def get_download_url(self, tenant_id: str, report_id: str) -> str | None:
        result = await self.db.execute(
            select(Report).where(
                Report.id == UUID(report_id),
                Report.tenant_id == UUID(tenant_id),
                Report.status == "ready",
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            return None

        try:
            import boto3
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION,
            )
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": report.file_url},
                ExpiresIn=3600,
            )
            return url
        except Exception:
            return report.file_url

    async def delete_report(self, tenant_id: str, report_id: str) -> bool:
        result = await self.db.execute(
            select(Report).where(
                Report.id == UUID(report_id),
                Report.tenant_id == UUID(tenant_id),
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            return False

        try:
            import boto3
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION,
            )
            s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=report.file_url)
        except Exception:
            pass

        await self.db.delete(report)
        await self.db.flush()
        return True

    async def generate_report(self, report_id: str) -> None:
        result = await self.db.execute(select(Report).where(Report.id == UUID(report_id)))
        report = result.scalar_one_or_none()
        if report is None:
            return

        try:
            slots_query = select(Slot).where(
                Slot.tenant_id == report.tenant_id,
                Slot.started_at >= report.period_start,
                Slot.ended_at <= report.period_end,
            )
            if report.terminal_ids:
                slots_query = slots_query.where(Slot.terminal_id.in_(report.terminal_ids))

            slots_result = await self.db.execute(slots_query)
            slots = slots_result.scalars().all()

            html_content = self._render_report_html(report, slots)

            import tempfile
            import os
            from weasyprint import HTML

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                HTML(string=html_content).write_pdf(tmp.name)
                file_size = os.path.getsize(tmp.name)

                try:
                    import boto3
                    s3_client = boto3.client(
                        "s3",
                        endpoint_url=settings.S3_ENDPOINT_URL,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.S3_REGION,
                    )
                    s3_key = f"{report.tenant_id}/reports/{report.id}.pdf"
                    s3_client.upload_file(tmp.name, settings.S3_BUCKET, s3_key)
                    report.file_url = s3_key
                except Exception:
                    report.file_url = tmp.name

                report.file_size_bytes = file_size
                report.status = "ready"

            os.unlink(tmp.name)
        except Exception:
            report.status = "failed"

        await self.db.flush()

    def _render_report_html(self, report: Report, slots: list) -> str:
        import html
        title_escaped = html.escape(report.title or "Report")
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>{title_escaped}</title></head>
        <body>
            <h1>{title_escaped}</h1>
            <p>Period: {html.escape(str(report.period_start))} to {html.escape(str(report.period_end))}</p>
            <p>Total slots: {len(slots)}</p>
        </body>
        </html>
        """
