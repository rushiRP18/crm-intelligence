"""Thread model — groups emails by conversation thread."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(500))
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # Open | Resolved | Escalated | Ignored
    status: Mapped[str] = mapped_column(String(50), default="Open", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)  # Auto-generated for 5+ email threads

    # Relationships
    emails: Mapped[list["Email"]] = relationship(
        "Email", back_populates="thread", order_by="Email.timestamp"
    )
    contact: Mapped["Contact | None"] = relationship(
        "Contact",
        foreign_keys=[sender_email],
        primaryjoin="Thread.sender_email == Contact.email",
        back_populates="threads",
    )

    __table_args__ = (
        Index("ix_threads_status", "status"),
        Index("ix_threads_last_updated", "last_updated_at"),
    )

    def __repr__(self) -> str:
        return f"<Thread {self.thread_id} [{self.status}]>"
