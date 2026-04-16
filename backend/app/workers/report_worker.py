import html as html_mod
import os
import tempfile
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.evaluation import Evaluation
from app.models.note import Note
from app.models.report import Report
from app.models.slot import Slot
from app.workers.celery_app import celery_app
from app.workers.db import get_sync_engine

logger = structlog.get_logger()


def _render_html(report: Report, slots: list, evaluations: dict, notes: list) -> str:
    rows = ""
    for slot in slots:
        ev = evaluations.get(str(slot.id))
        score = f"{float(ev.score_overall):.1f}" if ev and ev.score_overall else "N/A"
        sentiment = html_mod.escape(ev.sentiment_label) if ev and ev.sentiment_label else "N/A"
        language = html_mod.escape(slot.language) if slot.language else "N/A"
        rows += f"""
        <tr>
            <td>{slot.started_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td>{slot.duration_secs or 0}s</td>
            <td>{score}</td>
            <td>{sentiment}</td>
            <td>{language}</td>
        </tr>"""

    notes_html = ""
    if notes:
        for note in notes:
            safe_content = html_mod.escape(note.content)
            notes_html += f'<div style="margin:8px 0;padding:8px;border-left:3px solid #6366f1;"><p style="margin:0;font-size:13px;">{safe_content}</p><small style="color:#888;">{note.created_at.strftime("%Y-%m-%d %H:%M")}</small></div>'
    else:
        notes_html = "<p>No notes for this period.</p>"

    safe_title = html_mod.escape(report.title)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{safe_title}</title>
        <style>
            body {{ font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; color: #1e293b; margin: 40px; }}
            h1 {{ color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 8px; }}
            h2 {{ color: #334155; margin-top: 32px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
            th {{ background: #f1f5f9; padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e8f0; }}
            td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }}
            .meta {{ color: #64748b; font-size: 14px; }}
            .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 11px; }}
        </style>
    </head>
    <body>
        <h1>{safe_title}</h1>
        <p class="meta">Period: {report.period_start.strftime('%Y-%m-%d %H:%M')} &mdash; {report.period_end.strftime('%Y-%m-%d %H:%M')}</p>
        <p class="meta">Total interactions: {len(slots)}</p>
        <p class="meta">Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

        <h2>Interaction Summary</h2>
        <table>
            <thead>
                <tr><th>Time</th><th>Duration</th><th>Score</th><th>Sentiment</th><th>Language</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <h2>Notes</h2>
        {notes_html}

        <div class="footer">
            <p>Mutell &mdash; Generated Report</p>
        </div>
    </body>
    </html>
    """


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_report(self, report_id: str) -> None:
    logger.info("generating_report", report_id=report_id)
    engine = get_sync_engine()

    with Session(engine) as db:
        report = db.execute(
            select(Report).where(Report.id == UUID(report_id))
        ).scalar_one_or_none()

        if report is None:
            logger.error("report_not_found", report_id=report_id)
            return

        try:
            query = select(Slot).where(
                Slot.tenant_id == report.tenant_id,
                Slot.started_at >= report.period_start,
                Slot.ended_at <= report.period_end,
                Slot.status.in_(["evaluated", "unclear"]),
            )
            if report.terminal_ids:
                query = query.where(Slot.terminal_id.in_(report.terminal_ids))

            slots = db.execute(query.order_by(Slot.started_at)).scalars().all()

            slot_ids = [s.id for s in slots]
            if not slot_ids:
                eval_map = {}
            else:
                evals = db.execute(
                    select(Evaluation).where(Evaluation.slot_id.in_(slot_ids))
                ).scalars().all()
                eval_map = {str(e.slot_id): e for e in evals}

            if slot_ids:
                notes = db.execute(
                    select(Note).where(
                        Note.tenant_id == report.tenant_id,
                        Note.slot_id.in_(slot_ids),
                    ).order_by(Note.created_at)
                ).scalars().all()
            else:
                notes = []

            html = _render_html(report, slots, eval_map, notes)

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                from weasyprint import HTML
                HTML(string=html).write_pdf(tmp_path)
                file_size = os.path.getsize(tmp_path)

                s3_key = f"{report.tenant_id}/reports/{report.id}.pdf"

                try:
                    import boto3
                    s3_client = boto3.client(
                        "s3",
                        endpoint_url=settings.S3_ENDPOINT_URL,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        region_name=settings.S3_REGION,
                    )
                    s3_client.upload_file(tmp_path, settings.S3_BUCKET, s3_key)
                    report.file_url = s3_key
                except Exception as e:
                    logger.warning("s3_upload_failed", error=str(e))
                    report.status = "failed"
                    db.commit()
                    return

                report.file_size_bytes = file_size
                report.status = "ready"
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            db.commit()

            logger.info("report_generated", report_id=report_id, slots=len(slots))

        except Exception as e:
            logger.error("report_generation_failed", report_id=report_id, error=str(e))
            report.status = "failed"
            db.commit()
            raise self.retry(exc=e)
