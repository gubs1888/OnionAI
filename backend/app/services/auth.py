"""
Auth helpers: password hashing (PBKDF2) + JWT issue/verify + demo user seeding.

MVP security notes (honest scope):
  * PBKDF2-SHA256 with per-user salt — fine for the hackathon; swap for
    passlib/argon2 later if needed.
  * No refresh tokens, no complex RBAC — explicitly out of MVP scope.
  * DEMO login is seeded: username `demo`, password `demo123` (DEMO ONLY).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

_PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate, digest)


def create_access_token(user: User) -> tuple[str, int]:
    expires_in = settings.access_token_expire_minutes * 60
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    token = pyjwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_token(token: str) -> dict | None:
    try:
        return pyjwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except pyjwt.PyJWTError:
        return None


def ensure_demo_user(db: Session) -> User | None:
    """
    Seed the DEMO login (demo / demo123) exactly once, and only when the
    users table is empty. Idempotent. DEMO ONLY — never do this in production.
    """
    existing = db.query(User).first()
    if existing is not None:
        return existing
    if not settings.seed_demo_user:
        return None
    demo = User(
        username="demo",
        password_hash=hash_password("demo123"),
        role="operator",
    )
    db.add(demo)
    db.commit()
    db.refresh(demo)
    print("[auth] Seeded DEMO user: username='demo' password='demo123' (DEMO ONLY)")
    return demo
