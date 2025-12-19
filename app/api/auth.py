import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    is_refresh_token_revoked,
    revoke_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.schemas.token import RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.user_service import create_user, get_user_by_email

logger = logging.getLogger("app.auth")
_login_attempts: dict[str, list[float]] = defaultdict(list)

router = APIRouter(prefix="/auth", tags=["auth"])


def _prune_attempts(attempts: list[float]) -> None:
    now = time.monotonic()
    window = settings.login_attempts_window_seconds
    while attempts and now - attempts[0] > window:
        attempts.pop(0)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Регистрация доступна только для роли student",
        )
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    try:
        user = create_user(db, payload, role=payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = payload.email.lower()
    attempts = _login_attempts[email]
    _prune_attempts(attempts)
    if len(attempts) >= settings.login_attempts_limit:
        logger.warning("Exceeded login attempts for %s", email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток, повторите позже",
        )
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        attempts.append(time.monotonic())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    attempts.clear()
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "role": user.role.value})
    logger.info("User %s logged in", user.email)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(payload: RefreshRequest):
    try:
        token_data = decode_refresh_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if is_refresh_token_revoked(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    access_token = create_access_token(data={"sub": str(token_data.user_id), "role": token_data.role})
    new_refresh_token = create_refresh_token(data={"sub": str(token_data.user_id), "role": token_data.role})
    revoke_refresh_token(payload.refresh_token)
    logger.info("Refresh token rotated for user %s", token_data.user_id)
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout")
def logout(payload: RefreshRequest):
    if is_refresh_token_revoked(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token already revoked")
    try:
        token_data = decode_refresh_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    revoke_refresh_token(payload.refresh_token)
    logger.info("User %s logged out", token_data.user_id)
    return {"detail": "Logged out"}
