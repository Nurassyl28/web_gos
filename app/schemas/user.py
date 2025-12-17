from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, validator


def _normalize_email(value: str) -> str:
    cleaned = value.strip()
    if "@" not in cleaned or "." not in cleaned:
        raise ValueError("invalid email format")
    return cleaned.lower()


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    role: Literal["admin", "student"] = Field(default="student")

    _normalize_email = validator("email", allow_reuse=True)(_normalize_email)

    @validator("password")
    def password_max_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Пароль не должен превышать 72 байта для bcrypt")
        return value


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=1)

    _normalize_email = validator("email", allow_reuse=True)(_normalize_email)

    @validator("password")
    def password_max_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Пароль не должен превышать 72 байта для bcrypt")
        return value


class UserResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    email: str
    full_name: str | None
    role: str
    created_at: datetime


class UserInDB(UserResponse):
    hashed_password: str
