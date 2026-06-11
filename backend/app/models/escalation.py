"""Escalation model — records human escalations and legal/security flags."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    escalation_type: Mapped[str] = mapped_column(String(100))  # human|legal|security|compliance
    reason: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(50), default="High")  # Critical|High|Medium
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    # open | acknowledged | resolved
    status: Mapped[str] = mapped_column(String(50), default="open")
    brief: Mapped[str | None] = mapped_column(Text)  # Pre-filled context brief for human reviewer
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    email: Mapped["Email"] = relationship("Email", back_populates="escalations")

    def __repr__(self) -> str:
        return f"<Escalation {self.escalation_type} [{self.status}]>"
