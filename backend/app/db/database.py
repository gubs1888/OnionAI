"""
SQLAlchemy engine / session / Base.

Design notes
------------
* `get_db()` is the FastAPI dependency used by every endpoint.
* `init_db()` creates all tables from the ORM models. This keeps the backend
  startable on an EMPTY database (no migration step required for the MVP).
  Alembic can be added later under `app/db/migrations/` without changing any
  endpoint code.
* Works with PostgreSQL (docker-compose) and SQLite (zero-setup local dev).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import BACKEND_ROOT, settings

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

_connect_args = {}
if db_url.startswith("sqlite"):
    # SQLite needs this to work with FastAPI's threadpool.
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=_connect_args,
    pool_pre_ping=True,          # survive transient DB restarts
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for ALL ORM models."""


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables if they do not exist.

    SAFE TO RUN ON EVERY STARTUP. The backend must be able to start on an
    empty database — this is the "clean database initialization mechanism"
    for the MVP. A proper Alembic migration chain can replace this later
    (TEAM B) without touching endpoint code.
    """
    # Import for the side effect of registering every model on Base.metadata.
    from app.db import base as _models  # noqa: F401

    Base.metadata.create_all(bind=engine)


# Where uploaded images live relative to the backend root (used by static mount)
UPLOAD_DIR = BACKEND_ROOT / "uploads"
