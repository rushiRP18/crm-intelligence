"""
Audit Service — records all state changes to the immutable audit log.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    before_state: dict | None = None,
    after_state: dict | None = None,
    actor: str = "system",
    notes: str | None = None,
) -> AuditLog:
    """Create an immutable audit log entry."""
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_state=before_state,
        after_state=after_state,
        actor=actor,
        notes=notes,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
