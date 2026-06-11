"""
Email API routes.
Handles email ingestion, retrieval, and agent processing.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.email import Email
from app.models.thread import Thread
from app.models.contact import Contact
from app.schemas.email import EmailIngest, EmailResponse, EmailListResponse
from app.services.heuristic_filter import run_heuristic_filter
from app.services.audit_service import log_action
from app.utils.exceptions import EmailNotFound, DuplicateMessageId
from app.utils.logging import get_logger

router = APIRouter(prefix="/emails", tags=["Emails"])
logger = get_logger(__name__)


@router.post("/ingest", status_code=201)
def ingest_email(payload: EmailIngest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest a single email. Idempotent on message_id.
    Runs heuristic pre-filter synchronously, then triggers agent asynchronously.
    """
    # Idempotency check
    existing = db.query(Email).filter(Email.message_id == payload.message_id).first()
    if existing:
        raise DuplicateMessageId(payload.message_id)

    # Upsert contact
    contact = db.query(Contact).filter(Contact.email == payload.sender).first()
    if not contact:
        name_part = payload.sender.split('@')[0].replace('.', ' ').title()
        contact = Contact(email=payload.sender, name=name_part, status="Active")
        db.add(contact)
    contact.last_contact_at = datetime.utcnow()

    # Upsert thread
    thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
    if not thread:
        thread = Thread(
            thread_id=payload.thread_id,
            subject=payload.subject,
            sender_email=payload.sender,
            first_seen_at=payload.timestamp,
        )
        db.add(thread)
    thread.last_updated_at = datetime.utcnow()
    db.flush()

    # Run heuristic pre-filter (synchronous, sub-10ms)
    hflags = run_heuristic_filter(payload.sender, payload.subject, payload.body)

    # Create email record
    email = Email(
        message_id=payload.message_id,
        thread_id=thread.id,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        timestamp=payload.timestamp,
        status="spam" if hflags.is_spam else ("internal" if hflags.is_internal else "pending"),
        heuristic_flags={
            "is_spam": hflags.is_spam,
            "is_internal": hflags.is_internal,
            "is_security_threat": hflags.is_security_threat,
            "is_legal": hflags.is_legal,
            "is_gdpr": hflags.is_gdpr,
            "is_churn_risk": hflags.is_churn_risk,
            "is_compliance": hflags.is_compliance,
            "urgency_boost": hflags.urgency_boost,
            "priority_score": hflags.priority_score,
            "flags": hflags.flags,
        },
        category=hflags.initial_category,
    )
    db.add(email)
    db.commit()
    db.refresh(email)

    log_action(db, "email", email.id, "ingested", after_state={"sender": payload.sender, "thread_id": payload.thread_id})

    # Trigger agent processing in background (skip for spam/internal)
    if not hflags.is_spam and not hflags.is_internal:
        background_tasks.add_task(_process_email_async, email.id, db)

    logger.info(f"Ingested: {payload.message_id} from {payload.sender} [flags: {hflags.flags}]")
    return {
        "message": "Email ingested",
        "email_id": email.id,
        "message_id": payload.message_id,
        "heuristic_flags": hflags.flags,
    }


@router.post("/ingest/batch", status_code=201)
def ingest_batch(emails: list[EmailIngest], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Ingest multiple emails. Skips duplicates gracefully."""
    results = []
    for payload in emails:
        try:
            existing = db.query(Email).filter(Email.message_id == payload.message_id).first()
            if existing:
                results.append({"message_id": payload.message_id, "status": "duplicate_skipped"})
                continue

            contact = db.query(Contact).filter(Contact.email == payload.sender).first()
            if not contact:
                contact = Contact(
                    email=payload.sender,
                    name=payload.sender.split('@')[0].replace('.', ' ').title(),
                    status="Active",
                )
                db.add(contact)
            contact.last_contact_at = datetime.utcnow()

            thread = db.query(Thread).filter(Thread.thread_id == payload.thread_id).first()
            if not thread:
                thread = Thread(
                    thread_id=payload.thread_id,
                    subject=payload.subject,
                    sender_email=payload.sender,
                    first_seen_at=payload.timestamp,
                )
                db.add(thread)
            thread.last_updated_at = datetime.utcnow()
            db.flush()

            hflags = run_heuristic_filter(payload.sender, payload.subject, payload.body)
            email = Email(
                message_id=payload.message_id,
                thread_id=thread.id,
                sender=payload.sender,
                subject=payload.subject,
                body=payload.body,
                timestamp=payload.timestamp,
                status="spam" if hflags.is_spam else ("internal" if hflags.is_internal else "pending"),
                heuristic_flags={
                    "is_spam": hflags.is_spam,
                    "is_internal": hflags.is_internal,
                    "is_security_threat": hflags.is_security_threat,
                    "flags": hflags.flags,
                },
                category=hflags.initial_category,
            )
            db.add(email)
            db.commit()
            db.refresh(email)

            if not hflags.is_spam and not hflags.is_internal:
                background_tasks.add_task(_process_email_async, email.id, db)

            results.append({"message_id": payload.message_id, "email_id": email.id, "status": "ingested"})

        except Exception as e:
            db.rollback()
            results.append({"message_id": payload.message_id, "status": "error", "error": str(e)})

    return {"total": len(emails), "results": results}


def _process_email_async(email_id: int, db: Session):
    """Background task: run agent on email."""
    from app.agent.graph import run_agent
    from app.models.email import Email as EmailModel

    email = db.query(EmailModel).filter(EmailModel.id == email_id).first()
    if not email:
        return
    try:
        run_agent(
            db=db,
            email_id=email.id,
            message_id=email.message_id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            thread_id_str=db.query(Thread).filter(Thread.id == email.thread_id).first().thread_id,
            heuristic_flags=email.heuristic_flags or {},
            dry_run=False,
        )
    except Exception as e:
        logger.error(f"Background agent failed for email {email_id}: {e}")


@router.get("", response_model=EmailListResponse)
def list_emails(
    status: str | None = Query(None),
    category: str | None = Query(None),
    urgency: str | None = Query(None),
    requires_human: bool | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List emails with optional filters and pagination."""
    query = db.query(Email)
    if status:
        query = query.filter(Email.status == status)
    if category:
        query = query.filter(Email.category == category)
    if urgency:
        query = query.filter(Email.urgency == urgency)
    if requires_human is not None:
        query = query.filter(Email.requires_human == requires_human)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Email.subject.ilike(like)) | (Email.body.ilike(like)) | (Email.sender.ilike(like))
        )
    total = query.count()
    emails = query.order_by(Email.timestamp.desc()).offset(skip).limit(limit).all()
    return EmailListResponse(total=total, emails=[EmailResponse.model_validate(e) for e in emails])


@router.get("/{email_id}")
def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get full email detail including agent run, draft, and escalations."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise EmailNotFound(email_id)

    result = EmailResponse.model_validate(email).model_dump()

    if email.agent_run:
        result["agent_run"] = {
            "id": email.agent_run.id,
            "reasoning_trace": email.agent_run.reasoning_trace,
            "tool_calls": email.agent_run.tool_calls,
            "decision": email.agent_run.decision,
            "draft_reply": email.agent_run.draft_reply,
            "final_action": email.agent_run.final_action,
            "run_duration_ms": email.agent_run.run_duration_ms,
        }
    if email.draft:
        result["draft"] = {
            "id": email.draft.id,
            "body": email.draft.body,
            "status": email.draft.status,
            "tone": email.draft.tone,
            "policy_refs": email.draft.policy_refs,
        }
    if email.rag_retrieval:
        result["rag_context"] = email.rag_retrieval.chunks

    result["escalations"] = [
        {
            "type": e.escalation_type,
            "reason": e.reason,
            "priority": e.priority,
            "status": e.status,
        }
        for e in email.escalations
    ]
    return result


@router.post("/{email_id}/process")
def process_email(email_id: int, dry_run: bool = Query(False), db: Session = Depends(get_db)):
    """Manually trigger agent processing on an email."""
    from app.agent.graph import run_agent

    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise EmailNotFound(email_id)

    thread = db.query(Thread).filter(Thread.id == email.thread_id).first()
    final_state = run_agent(
        db=db,
        email_id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        thread_id_str=thread.thread_id if thread else "",
        heuristic_flags=email.heuristic_flags or {},
        dry_run=dry_run,
    )
    return {
        "email_id": email_id,
        "decision": final_state.get("decision"),
        "final_action": final_state.get("final_action"),
        "reasoning_trace": "\n".join(final_state.get("reasoning_trace", [])),
        "dry_run": dry_run,
    }
