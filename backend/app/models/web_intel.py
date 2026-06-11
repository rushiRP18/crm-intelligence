"""WebIntelCache model — caches web scraping results for 6 hours."""
from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WebIntelCache(Base):
    __tablename__ = "web_intel_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    scraped_data: Mapped[dict | None] = mapped_column(JSON)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<WebIntelCache {self.domain}>"
