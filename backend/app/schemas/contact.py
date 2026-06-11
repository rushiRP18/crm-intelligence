"""Pydantic schemas for contact profiles."""
from datetime import datetime
from pydantic import BaseModel


class ContactResponse(BaseModel):
    id: int
    email: str
    name: str | None
    company: str | None
    status: str
    account_value: float
    churn_risk_score: float
    created_at: datetime
    last_contact_at: datetime | None

    model_config = {"from_attributes": True}


class ContactStatusUpdate(BaseModel):
    status: str  # VIP | Blocked | Active | Churned
