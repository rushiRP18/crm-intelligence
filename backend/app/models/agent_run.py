"""AgentRun model — stores LangGraph agent execution traces."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    # Full Thought→Action→Observation trace as formatted string
    reasoning_trace: Mapped[str | None] = mapped_column(Text)
    # JSON list of {tool_name, input, output} for each tool call
    tool_calls: Mapped[list | None] = mapped_column(JSON)
    decision: Mapped[str | None] = mapped_column(String(100))  # draft_reply|escalate|flag_legal|etc
    draft_reply: Mapped[str | None] = mapped_column(Text)
    final_action: Mapped[str | None] = mapped_column(String(100))
    run_duration_ms: Mapped[float | None] = mapped_column(Float)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="agent_run")

    def __repr__(self) -> str:
        return f"<AgentRun email={self.email_id} decision={self.decision}>"
