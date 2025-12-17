from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.schemas.course import CourseCreate, CourseUpdate
from app.utils.exceptions import client_error


def _apply_course_filters(query, search: str | None, published_only: bool, is_published: bool | None):
    if published_only:
        query = query.filter(Course.is_published.is_(True))
    elif is_published is not None:
        query = query.filter(Course.is_published == is_published)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Course.title.ilike(pattern) | Course.description.ilike(pattern)
        )
    return query


def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    published_only: bool = True,
    is_published: bool | None = None,
) -> tuple[list[tuple[Course, int]], int]:
    limit = min(limit, 100)
    query = db.query(Course)
    query = _apply_course_filters(query, search, published_only, is_published)
    total = query.count()

    aggregated_query = (
        query
        .outerjoin(Enrollment)
        .with_entities(Course, func.count(Enrollment.id).label("students_count"))
        .group_by(Course.id)
        .order_by(Course.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = aggregated_query.all()
    return items, total


def get_course(db: Session, course_id: int) -> Course | None:
    return db.query(Course).filter(Course.id == course_id).first()


def create_course(db: Session, course_create: CourseCreate, creator_id: int) -> Course:
    existing = (
        db.query(Course)
        .filter(func.lower(Course.title) == course_create.title.lower())
        .first()
    )
    if existing:
        raise client_error("COURSE_EXISTS", "Курс с таким названием уже существует", field="title", status_code=400)

    course = Course(
        title=course_create.title,
        description=course_create.description,
        created_by=creator_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course: Course, payload: CourseUpdate) -> Course:
    if payload.title:
        duplicate = (
            db.query(Course)
            .filter(func.lower(Course.title) == payload.title.lower(), Course.id != course.id)
            .first()
        )
        if duplicate:
            raise client_error("COURSE_EXISTS", "Курс с таким названием уже существует", field="title", status_code=400)
        course.title = payload.title
    if payload.description is not None:
        course.description = payload.description
    if payload.is_published is not None:
        course.is_published = payload.is_published
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
