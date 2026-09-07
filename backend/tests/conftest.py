"""
Shared pytest fixtures for the backend.

Uses an in-memory SQLite DB (StaticPool) so tests are fast and never touch
the developer's real database. DEMO MODE is forced ON for determinism.
"""

import os

# MUST be set before app modules are imported (Settings reads env at import).
os.environ["DEMO_MODE"] = "true"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["SEED_DEMO_USER"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.db.database import Base  # noqa: E402
from app.db.base import (  # noqa: E402,F401  (registers all models)
    Assessment,
    Batch,
    Detection,
    Image,
    Report,
    User,
)
from app.main import app  # noqa: E402
from app.services.auth import ensure_demo_user  # noqa: E402

_test_engine = create_engine(
    "sqlite://",  # in-memory
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=_test_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session")
def client() -> TestClient:
    """TestClient with a seeded DEMO user."""
    with _TestingSession() as db:
        ensure_demo_user(db)
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()
