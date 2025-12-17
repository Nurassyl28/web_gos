from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.user import User
from app.utils.exceptions import client_error


def get_enrollment(db: Session, user_id: int, course_id: int) -> Enrollment | None:
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
    )


def create_enrollment(db: Session, user_id: int, course: Course) -> Enrollment:
    if not course.is_published:
        raise client_error("COURSE_UNPUBLISHED", "Курс не опубликован", status_code=404)
    existing = get_enrollment(db, user_id, course.id)
    if existing:
        raise client_error("ALREADY_ENROLLED", "Пользователь уже записан", status_code=409)
    enrollment = Enrollment(user_id=user_id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def list_student_enrollments(db: Session, user_id: int) -> list[Enrollment]:
    return db.query(Enrollment).filter(Enrollment.user_id == user_id).all()


def list_course_students(db: Session, course_id: int) -> list[User]:
    return (
        db.query(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.course_id == course_id)
        .all()
    )
