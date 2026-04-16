from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    title: str
    period_start: datetime
    period_end: datetime
    terminal_ids: list[str] | None = None
    include_transcripts: bool = False
    include_notes: bool = True
    accent_color: str | None = None


class ReportResponse(BaseModel):
    id: str
    tenant_id: str
    generated_by: str | None
    title: str
    period_start: datetime
    period_end: datetime
    terminal_ids: list | None
    file_url: str
    file_size_bytes: int | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int


class ReportDownloadResponse(BaseModel):
    download_url: str
    expires_in: int = 3600
