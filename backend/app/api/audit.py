"""Audit log API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/{entity_type}/{entity_id}")
def get_audit_history(
    entity_type: str,
    entity_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Retrieve the full audit log history for any entity (email, draft, contact, etc.).
    Each entry records who made what change and the before/after state.
    Supports pagination via skip/limit.
    """
    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "before": log.before_state,
                "after": log.after_state,
                "notes": log.notes,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }
