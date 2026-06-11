"""Contact model — CRM profile for each unique sender."""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    # VIP | Blocked | Active | Churned
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)
    account_value: Mapped[float] = mapped_column(Float, default=0.0)
    churn_risk_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 - 1.0
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    threads: Mapped[list["Thread"]] = relationship(
        "Thread", back_populates="contact", foreign_keys="Thread.sender_email",
        primaryjoin="Thread.sender_email == Contact.email",
    )

    __table_args__ = (
        Index("ix_contacts_status", "status"),
        Index("ix_contacts_churn_risk", "churn_risk_score"),
    )

    def __repr__(self) -> str:
        return f"<Contact {self.email} [{self.status}]>"
