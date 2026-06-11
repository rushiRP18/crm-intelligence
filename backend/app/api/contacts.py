"""Contact API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactResponse, ContactStatusUpdate
from app.utils.exceptions import ContactNotFound

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    status: str | None = Query(None, description="Filter by contact status (Active, VIP, Blocked, Churned)"),
    at_risk: bool = Query(False, description="If true, only return contacts with churn_risk_score > 0.6"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List contacts with optional status and churn-risk filters.
    Ordered by churn_risk_score descending (highest risk first).
    """
    query = db.query(Contact)
    if status:
        query = query.filter(Contact.status == status)
    if at_risk:
        query = query.filter(Contact.churn_risk_score > 0.6)
    return query.order_by(Contact.churn_risk_score.desc()).offset(skip).limit(limit).all()


@router.get("/{email}")
def get_contact(email: str, db: Session = Depends(get_db)):
    """
    Get a single contact by email address.
    Returns full contact data plus associated thread history.
    """
    contact = db.query(Contact).filter(Contact.email == email.lower()).first()
    if not contact:
        raise ContactNotFound(email)

    return {
        **ContactResponse.model_validate(contact).model_dump(),
        "thread_count": len(contact.threads),
        "threads": [
            {
                "thread_id": t.thread_id,
                "status": t.status,
                "subject": t.subject,
            }
            for t in contact.threads
        ],
    }


@router.patch("/{email}/status")
def update_contact_status(email: str, body: ContactStatusUpdate, db: Session = Depends(get_db)):
    """
    Update the status of a contact (VIP, Blocked, Active, Churned).
    Used by human agents to flag at-risk or high-value customers.
    """
    contact = db.query(Contact).filter(Contact.email == email.lower()).first()
    if not contact:
        raise ContactNotFound(email)

    valid_statuses = ["VIP", "Blocked", "Active", "Churned"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of: {valid_statuses}",
        )

    contact.status = body.status
    db.commit()
    return {"email": email, "status": body.status, "updated": True}
