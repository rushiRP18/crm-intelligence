"""Draft API routes."""
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.draft import Draft
from app.services.audit_service import log_action
from app.utils.exceptions import DraftNotFound

router = APIRouter(prefix="/drafts", tags=["Drafts"])


class DraftEditBody(BaseModel):
    """Request body for editing a draft reply."""
    body: str


@router.get("")
def list_drafts(
    status: str = "pending",
    db: Session = Depends(get_db),
):
    """
    List draft replies filtered by status.
    Default: pending (awaiting human approval).
    """
    drafts = (
        db.query(Draft)
        .filter(Draft.status == status)
        .order_by(Draft.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "email_id": d.email_id,
            "body": d.body,
            "status": d.status,
            "tone": d.tone,
            "policy_refs": d.policy_refs,
            "created_at": d.created_at,
        }
        for d in drafts
    ]


@router.patch("/{draft_id}")
def edit_draft(draft_id: int, body: DraftEditBody, db: Session = Depends(get_db)):
    """
    Edit the body of a draft reply.
    Records an audit log entry with the before/after state.
    """
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise DraftNotFound(draft_id)

    old_body = draft.body
    draft.body = body.body
    draft.updated_at = datetime.utcnow()
    db.commit()

    log_action(
        db,
        "draft",
        draft_id,
        "edited",
        before_state={"body": old_body[:100]},
        after_state={"body": body.body[:100]},
        actor="user",
    )
    return {"id": draft_id, "body": draft.body, "status": draft.status}


@router.post("/{draft_id}/approve")
def approve_draft(draft_id: int, approved_by: str = "user", db: Session = Depends(get_db)):
    """
    Approve and mark a draft as sent.
    Also updates the parent email status to 'resolved'.
    """
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise DraftNotFound(draft_id)

    draft.status = "sent"
    draft.approved_at = datetime.utcnow()
    draft.approved_by = approved_by

    # Mark parent email as resolved
    if draft.email:
        draft.email.status = "resolved"

    db.commit()

    log_action(db, "draft", draft_id, "approved_and_sent", actor=approved_by)
    return {
        "id": draft_id,
        "status": "sent",
        "approved_by": approved_by,
        "sent_at": draft.approved_at,
    }
