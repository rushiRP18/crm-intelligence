"""Thread API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.thread import Thread
from app.models.email import Email
from app.schemas.thread import ThreadResponse, ThreadListResponse
from app.schemas.email import EmailResponse
from app.utils.exceptions import ThreadNotFound

router = APIRouter(prefix="/threads", tags=["Threads"])


@router.get("", response_model=ThreadListResponse)
def list_threads(
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List all email threads with optional status filter and pagination.
    Returns thread metadata including email count.
    """
    query = db.query(Thread)
    if status:
        query = query.filter(Thread.status == status)
    total = query.count()
    threads = query.order_by(Thread.last_updated_at.desc()).offset(skip).limit(limit).all()

    result = []
    for t in threads:
        t_dict = {
            "id": t.id,
            "thread_id": t.thread_id,
            "subject": t.subject,
            "sender_email": t.sender_email,
            "first_seen_at": t.first_seen_at,
            "last_updated_at": t.last_updated_at,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "summary": t.summary,
            "email_count": len(t.emails),
            "emails": [],
        }
        result.append(t_dict)
    return ThreadListResponse(total=total, threads=result)


@router.get("/{thread_id}")
def get_thread(thread_id: str, db: Session = Depends(get_db)):
    """
    Get a single thread by its thread_id string, including all emails
    with agent reasoning traces and RAG chunks attached.
    """
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise ThreadNotFound(thread_id)

    emails_data = [EmailResponse.model_validate(e).model_dump() for e in thread.emails]

    # Enrich each email with agent run data and RAG chunks
    for i, email in enumerate(thread.emails):
        if email.agent_run:
            emails_data[i]["reasoning_trace"] = email.agent_run.reasoning_trace
            emails_data[i]["decision"] = email.agent_run.decision
        if email.rag_retrieval:
            emails_data[i]["rag_chunks"] = email.rag_retrieval.chunks

    return {
        "id": thread.id,
        "thread_id": thread.thread_id,
        "subject": thread.subject,
        "sender_email": thread.sender_email,
        "status": thread.status,
        "first_seen_at": thread.first_seen_at,
        "last_updated_at": thread.last_updated_at,
        "assigned_to": thread.assigned_to,
        "summary": thread.summary,
        "email_count": len(thread.emails),
        "emails": emails_data,
    }
