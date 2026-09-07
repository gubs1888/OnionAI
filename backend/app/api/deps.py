"""Shared FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.batch import Batch
from app.models.user import User
from app.services.auth import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Returns the JWT user when a valid token is supplied, else None.

    MVP scope: endpoints accept anonymous calls (demo-first). Swap this
    dependency for a strict variant when real auth enforcement is needed.
    """
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None
    try:
        return db.get(User, int(payload["sub"]))
    except (TypeError, ValueError):
        return None


def resolve_batch_ref(db: Session, batch_ref: str) -> Batch | None:
    """Accept either the numeric id ("1") or the batch code ("ON-0001")."""
    ref = (batch_ref or "").strip()
    if not ref:
        return None
    if ref.isdigit():
        batch = db.get(Batch, int(ref))
        if batch is not None:
            return batch
    return db.query(Batch).filter(Batch.batch_code.ilike(ref)).first()


def require_batch(db: Session, batch_ref: str) -> Batch:
    batch = resolve_batch_ref(db, batch_ref)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BATCH_NOT_FOUND", "message": f"Batch '{batch_ref}' not found."},
        )
    return batch
