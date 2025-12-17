from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email.lower()).first()


def create_user(db: Session, user_create: UserCreate, role: UserRole | str = UserRole.student) -> User:
    user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
        role=UserRole(role) if isinstance(role, str) else role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
