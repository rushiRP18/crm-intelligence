"""Pydantic schemas for thread responses."""
from datetime import datetime
from pydantic import BaseModel
from app.schemas.email import EmailResponse


class ThreadResponse(BaseModel):
    id: int
    thread_id: str
    subject: str | None
    sender_email: str
    first_seen_at: datetime
    last_updated_at: datetime
    status: str
    assigned_to: str | None
    summary: str | None
    email_count: int = 0
    emails: list[EmailResponse] = []

    model_config = {"from_attributes": True}


class ThreadListResponse(BaseModel):
    total: int
    threads: list[ThreadResponse]
