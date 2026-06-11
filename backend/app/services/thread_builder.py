"""
Thread Context Builder — assembles full conversation history for agent context.
"""
from sqlalchemy.orm import Session
from app.models.email import Email
from app.models.thread import Thread
from app.models.contact import Contact


def get_thread_context(db: Session, thread_id_str: str) -> list[dict]:
    """
    Return all emails in a thread as a list of dicts, ordered by timestamp.
    Used to build conversation history for the LLM prompt.
    """
    thread = db.query(Thread).filter(Thread.thread_id == thread_id_str).first()
    if not thread:
        return []

    emails = (
        db.query(Email)
        .filter(Email.thread_id == thread.id)
        .order_by(Email.timestamp.asc())
        .all()
    )

    return [
        {
            "message_id": e.message_id,
            "sender": e.sender,
            "subject": e.subject,
            "body": e.body,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "category": e.category,
            "sentiment": e.sentiment,
        }
        for e in emails
    ]


def get_thread_summary_context(thread_history: list[dict]) -> str:
    """
    Format thread history as a readable string for LLM prompt injection.
    """
    if not thread_history:
        return "No previous conversation history."

    lines = []
    for i, msg in enumerate(thread_history, 1):
        lines.append(
            f"Message {i} [{msg.get('timestamp', 'unknown time')}] "
            f"From: {msg.get('sender', 'unknown')}\n"
            f"Subject: {msg.get('subject', '(no subject)')}\n"
            f"Body: {msg.get('body', '(empty)')[:500]}\n"
        )
    return "\n---\n".join(lines)


def get_sender_history(db: Session, sender_email: str, limit: int = 20) -> list[dict]:
    """
    Return all emails from a specific sender across all threads.
    Used by get_thread_history agent tool.
    """
    emails = (
        db.query(Email)
        .filter(Email.sender == sender_email.lower())
        .order_by(Email.timestamp.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "message_id": e.message_id,
            "subject": e.subject,
            "body": (e.body or "")[:300],
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "category": e.category,
            "sentiment": e.sentiment,
            "sentiment_score": e.sentiment_score,
            "status": e.status,
        }
        for e in emails
    ]


def should_generate_summary(thread_email_count: int) -> bool:
    """Threads with 5+ emails get an auto-generated summary (bonus feature)."""
    return thread_email_count >= 5
