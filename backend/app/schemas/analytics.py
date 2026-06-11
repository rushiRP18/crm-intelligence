"""Pydantic schemas for analytics endpoints."""
from pydantic import BaseModel
from datetime import datetime


class SentimentPoint(BaseModel):
    date: str
    avg_score: float
    email_count: int


class SentimentTrendResponse(BaseModel):
    sender: str | None
    days: int
    data_points: list[SentimentPoint]


class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    total: int
    categories: list[CategoryCount]


class DashboardSummary(BaseModel):
    total_emails: int
    pending: int
    escalated: int
    needs_human: int
    auto_replied: int
    spam: int
    avg_confidence: float
    avg_sentiment_score: float
    escalation_rate: float
    auto_reply_rate: float
    at_risk_contacts: int
