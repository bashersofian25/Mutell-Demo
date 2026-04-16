from datetime import datetime
from pydantic import BaseModel


class SlotPayload(BaseModel):
    started_at: datetime
    ended_at: datetime
    raw_text: str
    metadata: dict[str, str] | None = None
