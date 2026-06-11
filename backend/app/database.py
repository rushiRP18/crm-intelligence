"""
SQLAlchemy database engine, session factory, and base model.
Uses SQLite with async-safe configuration for development.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import get_settings


settings = get_settings()


def _get_engine():
    """Create SQLAlchemy engine with SQLite-specific settings."""
    if "sqlite" in settings.database_url:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,   # set to True only for deep DB debugging; use silence_sqlalchemy_logs() otherwise
        )
        # Enable WAL mode for better concurrent read performance
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        return engine
    else:
        return create_engine(settings.database_url, echo=False)


engine = _get_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """FastAPI dependency — yields a DB session and ensures cleanup."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (used on startup if migrations not run yet)."""
    from app.models import (  # noqa: F401 — import all models for metadata
        contact, thread, email, agent_run, draft, ticket,
        escalation, audit_log, web_intel, rag_retrieval
    )
    Base.metadata.create_all(bind=engine)
