"""Ticket API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ticket import Ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("")
def list_tickets(
    status: str | None = Query(None, description="Filter by ticket status (open, in_progress, resolved, closed)"),
    priority: str | None = Query(None, description="Filter by priority (low, medium, high, critical)"),
    ticket_type: str | None = Query(None, description="Filter by ticket type (bug, churn_risk, legal, security, etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List support/escalation tickets with optional filtering by status,
    priority, and type. Results are ordered by creation date descending
    (most recent first).
    """
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if ticket_type:
        query = query.filter(Ticket.ticket_type == ticket_type)
    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "status": t.status,
            "type": t.ticket_type,
            "assignee": t.assignee,
            "created_at": t.created_at,
        }
        for t in tickets
    ]


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Get full details for a single ticket by ID.
    Includes the full ticket body, resolution timestamp, and linked email.
    """
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TICKET_NOT_FOUND",
                "message": f"Ticket {ticket_id} not found",
            },
        )
    return {
        "id": t.id,
        "email_id": t.email_id,
        "title": t.title,
        "body": t.body,
        "priority": t.priority,
        "status": t.status,
        "type": t.ticket_type,
        "assignee": t.assignee,
        "created_at": t.created_at,
        "resolved_at": t.resolved_at,
    }
