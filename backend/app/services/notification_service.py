import asyncio
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _send_email(self, to: str, subject: str, body: str) -> bool:
        if not settings.SMTP_HOST:
            return False
        try:
            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
            return True
        except Exception:
            return False

    async def _send_email_async(self, to: str, subject: str, body: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._send_email, to, subject, body)

    async def send_user_invited(self, email: str, invite_token: str) -> None:
        accept_url = f"{settings.ALLOWED_ORIGINS.split(',')[0].strip()}/invite/{invite_token}"
        await self._send_email_async(
            to=email,
            subject="You've been invited to Mutell",
            body=f"<p>You've been invited. <a href='{accept_url}'>Accept your invitation</a></p>",
        )

    async def send_password_reset(self, email: str, reset_token: str) -> None:
        reset_url = f"{settings.ALLOWED_ORIGINS.split(',')[0].strip()}/reset-password/{reset_token}"
        await self._send_email_async(
            to=email,
            subject="Password Reset Request",
            body=f"<p>Click <a href='{reset_url}'>here</a> to reset your password. This link expires in 1 hour.</p>",
        )

    async def send_report_ready(self, user_email: str, report_title: str) -> None:
        await self._send_email_async(
            to=user_email,
            subject=f"Report Ready: {report_title}",
            body=f"<p>Your report <strong>{report_title}</strong> is ready for download.</p>",
        )

    async def send_report_failed(self, user_email: str, report_title: str) -> None:
        await self._send_email_async(
            to=user_email,
            subject=f"Report Generation Failed: {report_title}",
            body=f"<p>Report <strong>{report_title}</strong> failed to generate. Please try again.</p>",
        )

    async def send_low_score_alert(self, tenant_admin_email: str, slot_id: str, score: float) -> None:
        await self._send_email_async(
            to=tenant_admin_email,
            subject=f"Low Score Alert: {score:.1f}/100",
            body=f"<p>Slot {slot_id} received a score of <strong>{score:.1f}</strong>, which is below the alert threshold.</p>",
        )

    async def send_evaluation_failed(self, tenant_admin_email: str, slot_id: str) -> None:
        await self._send_email_async(
            to=tenant_admin_email,
            subject=f"Evaluation Failed: {slot_id}",
            body=f"<p>The AI evaluation for slot {slot_id} failed after all retry attempts.</p>",
        )

    async def send_tenant_suspended(self, admin_email: str) -> None:
        await self._send_email_async(
            to=admin_email,
            subject="Account Suspended",
            body="<p>Your Mutell account has been suspended. Please contact support.</p>",
        )

    async def send_plan_limit_warning(self, admin_email: str, usage_pct: float) -> None:
        await self._send_email_async(
            to=admin_email,
            subject=f"Plan Limit Warning: {usage_pct:.0f}% Usage",
            body=f"<p>You've used {usage_pct:.0f}% of your daily slot quota. Consider upgrading your plan.</p>",
        )
