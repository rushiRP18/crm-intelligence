"""Ticket model — internal support/engineering tickets."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("emails.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(50), default="Medium")  # Critical|High|Medium|Low
    status: Mapped[str] = mapped_column(String(50), default="Open")    # Open|In Progress|Resolved|Closed
    ticket_type: Mapped[str | None] = mapped_column(String(100))       # bug|compliance|legal|support
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    email: Mapped["Email | None"] = relationship("Email", back_populates="tickets")

    def __repr__(self) -> str:
        return f"<Ticket #{self.id} [{self.status}]>"
