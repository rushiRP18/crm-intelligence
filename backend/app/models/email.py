"""Email model — individual email messages with classification results."""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Boolean, Text, Integer, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("threads.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # pending | processing | classified | escalated | resolved | spam | internal
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    # Classification results (populated after AI processing)
    category: Mapped[str | None] = mapped_column(String(100))  # Complaint|Inquiry|Bug Report|etc
    sentiment: Mapped[str | None] = mapped_column(String(50))  # Positive|Neutral|Negative|Mixed
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    urgency: Mapped[str | None] = mapped_column(String(50))   # Critical|High|Medium|Low
    requires_human: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    escalation_reason: Mapped[str | None] = mapped_column(Text)
    suggested_reply: Mapped[str | None] = mapped_column(Text)
    detected_entities: Mapped[dict | None] = mapped_column(JSON)  # order_ids, ticket_ids, etc
    heuristic_flags: Mapped[dict | None] = mapped_column(JSON)   # spam_score, security_flag, etc
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    thread: Mapped["Thread"] = relationship("Thread", back_populates="emails")
    agent_run: Mapped["AgentRun | None"] = relationship("AgentRun", back_populates="email", uselist=False)
    draft: Mapped["Draft | None"] = relationship("Draft", back_populates="email", uselist=False)
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="email")
    escalations: Mapped[list["Escalation"]] = relationship("Escalation", back_populates="email")
    rag_retrieval: Mapped["RagRetrieval | None"] = relationship("RagRetrieval", back_populates="email", uselist=False)

    __table_args__ = (
        Index("ix_emails_status", "status"),
        Index("ix_emails_category", "category"),
        Index("ix_emails_urgency", "urgency"),
        Index("ix_emails_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Email {self.message_id} [{self.status}]>"
