from pydantic import BaseModel


class NotificationSettingsResponse(BaseModel):
    email_evaluations: bool
    email_failures: bool
    email_reports: bool
    push_mentions: bool
    push_weekly_summary: bool

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    email_evaluations: bool
    email_failures: bool
    email_reports: bool
    push_mentions: bool
    push_weekly_summary: bool
