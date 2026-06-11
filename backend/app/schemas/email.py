"""Pydantic schemas for email ingestion and classification output."""
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Any


class DetectedEntities(BaseModel):
    order_ids: list[str] = []
    ticket_ids: list[str] = []
    monetary_amounts: list[str] = []
    deadlines: list[str] = []
    products_mentioned: list[str] = []


class EmailIngest(BaseModel):
    """Schema for incoming email payload (POST /api/ingest)."""
    message_id: str
    sender: str
    subject: str | None = None
    body: str | None = None
    timestamp: datetime
    thread_id: str

    @field_validator("body", mode="before")
    @classmethod
    def truncate_long_body(cls, v):
        """Truncate very long bodies to 8000 chars to avoid LLM token overflow."""
        if v and len(v) > 8000:
            return v[:8000] + "\n\n[... body truncated for processing ...]"
        return v

    @field_validator("sender", mode="before")
    @classmethod
    def lowercase_sender(cls, v):
        return v.strip().lower() if v else v


class ClassificationOutput(BaseModel):
    """Structured output from LLM classification — matches assessment schema exactly."""
    category: str  # Complaint|Inquiry|Bug Report|Feature Request|Compliance|Legal|Billing|Spam|Internal|Other
    sentiment: str  # Positive|Neutral|Negative|Mixed
    sentiment_score: float  # -1.0 to +1.0
    urgency: str  # Critical|High|Medium|Low
    requires_human: bool
    escalation_reason: str | None = None
    suggested_reply: str | None = None
    confidence: float  # 0.0 to 1.0
    detected_entities: DetectedEntities = DetectedEntities()


class EmailResponse(BaseModel):
    """Full email response with classification."""
    id: int
    message_id: str
    thread_id: int
    sender: str
    subject: str | None
    body: str | None
    timestamp: datetime
    status: str
    category: str | None
    sentiment: str | None
    sentiment_score: float | None
    urgency: str | None
    requires_human: bool
    confidence: float | None
    escalation_reason: str | None
    detected_entities: Any | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailListResponse(BaseModel):
    total: int
    emails: list[EmailResponse]
