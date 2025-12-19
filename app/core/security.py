from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
_revoked_refresh_tokens: set[str] = set()


class TokenData(BaseModel):
    user_id: int
    role: str
    jti: str | None = None


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _build_token(data: dict[str, Any], expires_delta: timedelta | None, token_type: str, extra: dict[str, Any] | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "type": token_type})
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    return _build_token(data, expires_delta, "access")


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    jti = str(uuid4())
    extra = {"jti": jti}
    return _build_token(data, expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes), "refresh", extra)


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload.get("sub"))
        role = payload.get("role")
        if user_id is None or role is None:
            raise JWTError()
        return TokenData(user_id=user_id, role=role, jti=payload.get("jti"))
    except JWTError as exc:
        raise JWTError("Token invalid") from exc


def decode_refresh_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise JWTError("Not refresh token")
        user_id = int(payload.get("sub"))
        role = payload.get("role")
        jti = payload.get("jti")
        if user_id is None or role is None or jti is None:
            raise JWTError()
        return TokenData(user_id=user_id, role=role, jti=jti)
    except JWTError as exc:
        raise JWTError("Refresh token invalid") from exc


def is_refresh_token_revoked(token: str) -> bool:
    return token in _revoked_refresh_tokens


def revoke_refresh_token(token: str) -> None:
    _revoked_refresh_tokens.add(token)
