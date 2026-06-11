"""Draft model — AI-generated reply drafts pending human review."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str | None] = mapped_column(String(100))   # empathetic|professional|formal
    policy_refs: Mapped[list | None] = mapped_column(JSON)  # list of policy doc names cited
    # pending | approved | rejected | sent
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="draft")

    def __repr__(self) -> str:
        return f"<Draft email={self.email_id} [{self.status}]>"
