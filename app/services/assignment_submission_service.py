from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.assignment_submission import AssignmentSubmission
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.assignment_submission import AssignmentSubmissionCreate


def get_submission(db: Session, assignment_id: int, user_id: int) -> AssignmentSubmission | None:
    return (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.user_id == user_id,
        )
        .order_by(AssignmentSubmission.submitted_at.desc())
        .first()
    )


def list_submissions_for_assignment(db: Session, assignment_id: int) -> list[AssignmentSubmission]:
    return (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .all()
    )


def list_submissions_for_user(db: Session, user_id: int) -> list[AssignmentSubmission]:
    return (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.user_id == user_id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .all()
    )


def list_submission_overview(db: Session):
    return (
        db.query(AssignmentSubmission, Assignment, Course, User)
        .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
        .join(Course, Assignment.course_id == Course.id)
        .join(User, AssignmentSubmission.user_id == User.id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .all()
    )


def _ensure_enrolled(db: Session, user_id: int, course_id: int) -> bool:
    return (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        .first()
        is not None
    )


def create_submission(
    db: Session,
    user_id: int,
    assignment: Assignment,
    payload: AssignmentSubmissionCreate,
) -> AssignmentSubmission:
    if not _ensure_enrolled(db, user_id, assignment.course_id):
        raise ValueError("Student is not enrolled in the assignment course")
    submission = AssignmentSubmission(
        assignment_id=assignment.id,
        user_id=user_id,
        message=payload.message,
        link=str(payload.link) if payload.link else None,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission
