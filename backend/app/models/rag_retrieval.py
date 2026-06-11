"""RagRetrieval model — logs what knowledge chunks were used per email."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RagRetrieval(Base):
    __tablename__ = "rag_retrievals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False, unique=True)
    query: Mapped[str | None] = mapped_column(Text)
    # List of {content, source, score} dicts
    chunks: Mapped[list | None] = mapped_column(JSON)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    email: Mapped["Email"] = relationship("Email", back_populates="rag_retrieval")

    def __repr__(self) -> str:
        return f"<RagRetrieval email={self.email_id}>"
