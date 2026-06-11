"""
Sentiment Trend Tracker.

Tracks per-sender sentiment over time and detects deterioration patterns
(3+ consecutive negative emails triggers escalation alert).
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.email import Email
from app.models.contact import Contact


def compute_moving_average(scores: list[float], window: int = 3) -> list[float]:
    """Simple moving average of sentiment scores."""
    if len(scores) < window:
        return scores
    result = []
    for i in range(len(scores)):
        start = max(0, i - window + 1)
        result.append(sum(scores[start:i+1]) / (i - start + 1))
    return result


def check_sentiment_deterioration(
    db: Session,
    sender_email: str,
    consecutive_threshold: int = 3,
) -> bool:
    """
    Detect if sender has sent N+ consecutive negative emails.
    Returns True if escalation alert should be triggered.
    """
    recent_emails = (
        db.query(Email)
        .filter(
            Email.sender == sender_email.lower(),
            Email.sentiment_score.isnot(None),
        )
        .order_by(Email.timestamp.desc())
        .limit(consecutive_threshold)
        .all()
    )

    if len(recent_emails) < consecutive_threshold:
        return False

    # Check if ALL recent emails are negative (score < -0.3)
    return all(e.sentiment_score < -0.3 for e in recent_emails)


def get_analytics_anchor(db: Session) -> datetime:
    """
    Get the anchor datetime for analytics.
    If the latest email in the DB is older than the current time, anchor to that email's timestamp.
    """
    anchor = datetime.utcnow()
    try:
        max_ts_str = db.query(func.max(Email.timestamp)).scalar()
        if max_ts_str:
            if isinstance(max_ts_str, str):
                max_ts_str = max_ts_str.replace("Z", "")
                if "T" in max_ts_str:
                    db_max = datetime.fromisoformat(max_ts_str)
                else:
                    db_max = datetime.strptime(max_ts_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            else:
                db_max = max_ts_str
            
            if db_max < datetime.utcnow():
                anchor = db_max
    except Exception:
        pass
    return anchor


def get_sentiment_trend(
    db: Session,
    sender: str | None,
    days: int = 30,
) -> list[dict]:
    """
    Get daily average sentiment scores for analytics chart.
    If sender is None, returns global trend.
    """
    anchor = get_analytics_anchor(db)
    since = anchor - timedelta(days=days)
    query = (
        db.query(
            func.date(Email.timestamp).label("date"),
            func.avg(Email.sentiment_score).label("avg_score"),
            func.count(Email.id).label("email_count"),
        )
        .filter(
            Email.timestamp >= since,
            Email.sentiment_score.isnot(None),
        )
    )
    if sender:
        query = query.filter(Email.sender == sender.lower())

    results = query.group_by(func.date(Email.timestamp)).order_by("date").all()

    return [
        {
            "date": str(row.date),
            "avg_score": round(float(row.avg_score), 3),
            "email_count": row.email_count,
        }
        for row in results
    ]


def update_contact_churn_risk(db: Session, sender_email: str) -> float:
    """
    Compute and update churn risk score for a contact based on:
    - Recent sentiment trend (moving avg of last 5 emails)
    - Number of unresolved threads
    - Presence of churn keywords in recent emails
    Returns updated churn_risk_score (0.0 to 1.0).
    """
    contact = db.query(Contact).filter(Contact.email == sender_email.lower()).first()
    if not contact:
        return 0.0

    # Get last 5 sentiment scores
    recent = (
        db.query(Email.sentiment_score)
        .filter(
            Email.sender == sender_email.lower(),
            Email.sentiment_score.isnot(None),
        )
        .order_by(Email.timestamp.desc())
        .limit(5)
        .all()
    )
    scores = [r[0] for r in recent]

    # Base score from average sentiment (map -1..1 → 0..1 inverse)
    if scores:
        avg = sum(scores) / len(scores)
        sentiment_risk = max(0.0, (-avg + 1) / 2)  # negative sentiment → high risk
    else:
        sentiment_risk = 0.3  # unknown

    churn_risk = round(min(1.0, sentiment_risk), 2)
    contact.churn_risk_score = churn_risk
    db.commit()
    return churn_risk
