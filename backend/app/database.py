"""
database.py — SQLAlchemy database engine and session management.

This module sets up the core database connection for the application:
  - Engine: actual connection to PostgreSQL
  - SessionLocal: database session factory (one session per request)
  - Base: declarative base that all ORM models inherit from
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SQLAlchemy Engine
# ---------------------------------------------------------------------------
# The engine is the core interface to the database.
# pool_pre_ping=True detects stale connections and reconnects automatically.
# For SQLite: check_same_thread=False allows FastAPI's multi-threaded request handling.
_engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,  # Set True for SQL query logging during development
}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **_engine_kwargs)


# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------
# SessionLocal is a factory class; each call creates a new database session.
# autocommit=False: transactions must be committed explicitly
# autoflush=False: changes are not automatically written to DB before queries
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
# All ORM model classes must inherit from Base.
# SQLAlchemy uses this to track table definitions.
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Yields a session and ensures it is closed after the request completes,
    even if an exception occurs. Use with FastAPI's Depends().

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables defined in ORM models.

    Called on application startup. Safe to call multiple times —
    SQLAlchemy will not recreate existing tables.
    """
    # Import all models so SQLAlchemy knows about them before create_all
    from app.models import (  # noqa: F401
        user,
        medicine,
        order,
        prescription,
        refill_alert,
        webhook_event,
        symptom_session,
    )

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Seed default admin if missing
    from app.models.user import User
    from app.utils.security import hash_password
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            logger.info("Seeding default admin user...")
            admin = User(
                name="Admin",
                email="admin@pharmaagent.com",
                password_hash=hash_password("admin123"),
                role="admin",
                is_approved=1
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created: admin@pharmaagent.com")
    except Exception as e:
        logger.error(f"Error seeding admin: {e}")
        db.rollback()
    finally:
        db.close()
        
    logger.info("Database tables ready.")
