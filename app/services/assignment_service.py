from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.utils.exceptions import client_error


def get_assignment(db: Session, assignment_id: int) -> Assignment | None:
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()


def list_assignments_for_course(db: Session, course_id: int) -> list[Assignment]:
    return (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id)
        .order_by(Assignment.due_date.asc().nulls_last(), Assignment.created_at.desc())
        .all()
    )


def list_assignments_for_user(db: Session, user) -> list[Assignment]:
    if user.role == UserRole.admin:
        return db.query(Assignment).order_by(Assignment.due_date.asc().nulls_last(), Assignment.created_at.desc()).all()
    course_ids = (
        db.query(Enrollment.course_id)
        .filter(Enrollment.user_id == user.id)
        .subquery()
    )
    return (
        db.query(Assignment)
        .filter(Assignment.course_id.in_(course_ids))
        .order_by(Assignment.due_date.asc().nulls_last(), Assignment.created_at.desc())
        .all()
    )


def create_assignment(db: Session, course: Course, payload: AssignmentCreate) -> Assignment:
    assignment = Assignment(
        course_id=course.id,
        title=payload.title,
        description=payload.description,
        link=str(payload.link) if payload.link else None,
        due_date=payload.due_date,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def update_assignment(db: Session, assignment: Assignment, payload: AssignmentUpdate) -> Assignment:
    if payload.title:
        assignment.title = payload.title
    if payload.description is not None:
        assignment.description = payload.description
    if payload.link is not None:
        assignment.link = str(payload.link) if payload.link else None
    if payload.due_date is not None:
        assignment.due_date = payload.due_date
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, assignment: Assignment) -> None:
    db.delete(assignment)
    db.commit()
