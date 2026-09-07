"""GET /api/health — liveness + honest dependency status."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Service health check",
    description=(
        "Returns service status, version, REAL database connectivity and whether "
        "DEMO MODE is active. The database field is never faked: it reflects an "
        "actual `SELECT 1` probe."
    ),
)
def health(db: Session = Depends(get_db)) -> dict:
    database_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — health must never lie or crash
        database_status = "disconnected"

    return {
        "status": "ok" if database_status == "connected" else "degraded",
        "service": settings.app_name,
        "version": settings.version,
        "database": database_status,
        "demo_mode": settings.demo_mode,
        "time": datetime.now(timezone.utc).isoformat(),
    }
