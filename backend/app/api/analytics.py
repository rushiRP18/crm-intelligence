"""Analytics API routes."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.email import Email
from app.models.contact import Contact
from app.services.sentiment_tracker import get_sentiment_trend, get_analytics_anchor
from app.schemas.analytics import (
    SentimentTrendResponse,
    SentimentPoint,
    CategoryBreakdownResponse,
    CategoryCount,
    DashboardSummary,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/sentiment-trend", response_model=SentimentTrendResponse)
def sentiment_trend(
    sender: str | None = Query(None, description="Filter trend by sender email"),
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    db: Session = Depends(get_db),
):
    """
    Return daily average sentiment scores over the requested time window.
    Optionally scoped to a single sender for per-contact trend analysis.
    """
    data = get_sentiment_trend(db, sender, days)
    return SentimentTrendResponse(
        sender=sender,
        days=days,
        data_points=[SentimentPoint(**p) for p in data],
    )


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def category_breakdown(
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    db: Session = Depends(get_db),
):
    """
    Return a breakdown of email volume by category with percentage share.
    Useful for understanding workload composition over time.
    """
    anchor = get_analytics_anchor(db)
    since = anchor - timedelta(days=days)
    rows = (
        db.query(Email.category, func.count(Email.id).label("count"))
        .filter(Email.timestamp >= since, Email.category.isnot(None))
        .group_by(Email.category)
        .all()
    )
    total = sum(r.count for r in rows)
    categories = [
        CategoryCount(
            category=r.category,
            count=r.count,
            percentage=round(r.count / total * 100, 1) if total else 0,
        )
        for r in sorted(rows, key=lambda x: x.count, reverse=True)
    ]
    return CategoryBreakdownResponse(total=total, categories=categories)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    """
    Return a high-level dashboard summary: email counts by status,
    agent confidence, sentiment averages, escalation/auto-reply rates,
    and count of at-risk contacts.
    """
    total = db.query(Email).count()
    pending = db.query(Email).filter(Email.status == "pending").count()
    escalated = db.query(Email).filter(Email.status == "escalated").count()
    needs_human = db.query(Email).filter(Email.requires_human == True).count()
    auto_replied = db.query(Email).filter(Email.status == "resolved").count()
    spam = db.query(Email).filter(Email.status == "spam").count()
    internal_count = db.query(Email).filter(Email.status == "internal").count()
    at_risk = db.query(Contact).filter(Contact.churn_risk_score > 0.6).count()

    avg_conf = (
        db.query(func.avg(Email.confidence))
        .filter(Email.confidence.isnot(None))
        .scalar() or 0
    )
    avg_sent = (
        db.query(func.avg(Email.sentiment_score))
        .filter(Email.sentiment_score.isnot(None))
        .scalar() or 0
    )

    # Processable = all emails that went through the agent pipeline
    processable = total - spam - internal_count
    escalation_rate = round(escalated / processable * 100, 1) if processable else 0
    auto_reply_rate = round(auto_replied / processable * 100, 1) if processable else 0

    return DashboardSummary(
        total_emails=total,
        pending=pending,
        escalated=escalated,
        needs_human=needs_human,
        auto_replied=auto_replied,
        spam=spam,
        avg_confidence=round(float(avg_conf), 3),
        avg_sentiment_score=round(float(avg_sent), 3),
        escalation_rate=escalation_rate,
        auto_reply_rate=auto_reply_rate,
        at_risk_contacts=at_risk,
    )
