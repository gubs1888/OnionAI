"""POST /api/auth/login — MVP JWT login (demo user seeded in DEMO MODE)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.batch import LoginRequest, TokenOut, UserOut
from app.models.user import User
from app.services.auth import create_access_token, ensure_demo_user, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Log in and receive a JWT access token",
    description=(
        "JSON body: {\"username\", \"password\"}. "
        "In DEMO MODE a user `demo` / `demo123` is seeded automatically. "
        "Returns a bearer token for optional use on other endpoints "
        "(MVP endpoints currently accept anonymous calls)."
    ),
    responses={401: {"description": "Invalid credentials"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    ensure_demo_user(db)  # idempotent; only seeds when the table is empty

    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password."},
        )

    token, expires_in = create_access_token(user)
    return TokenOut(access_token=token, token_type="bearer", expires_in=expires_in,
                    user=UserOut.model_validate(user))
