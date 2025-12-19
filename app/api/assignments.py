from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from app.schemas.assignment_submission import (
    AssignmentSubmissionCreate,
    AssignmentSubmissionOverview,
    AssignmentSubmissionResponse,
)
from app.services.assignment_service import (
    create_assignment,
    delete_assignment,
    get_assignment,
    list_assignments_for_course,
    list_assignments_for_user,
    update_assignment,
)
from app.services.assignment_submission_service import (
    create_submission,
    list_submission_overview,
    list_submissions_for_assignment,
    list_submissions_for_user,
)
from app.services.course_service import get_course
from app.services.enrollment_service import get_enrollment

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/", response_model=list[AssignmentResponse])
def read_my_assignments(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    assignments = list_assignments_for_user(db, current_user)
    return assignments


@router.get("/courses/{course_id}", response_model=list[AssignmentResponse])
def read_course_assignments(course_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    course = get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    if current_user.role != UserRole.admin:
        enrollment = get_enrollment(db, current_user.id, course_id)
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
    return list_assignments_for_course(db, course_id)


@router.get("/submissions", response_model=list[AssignmentSubmissionResponse])
def read_my_submissions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    submissions = list_submissions_for_user(db, current_user.id)
    return submissions


@router.get("/{assignment_id}/submissions", response_model=list[AssignmentSubmissionResponse])
def read_assignment_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    assignment = get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
    submissions = list_submissions_for_assignment(db, assignment_id)
    return submissions


@router.get("/admin-overview", response_model=list[AssignmentSubmissionOverview])
def read_all_submissions(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    records = list_submission_overview(db)
    return [
        AssignmentSubmissionOverview(
            submission_id=submission.id,
            assignment_id=assignment.id,
            assignment_title=assignment.title,
            course_id=course.id,
            course_title=course.title,
            student_id=user.id,
            student_email=user.email,
            message=submission.message,
            link=submission.link,
            submitted_at=submission.submitted_at,
        )
        for submission, assignment, course, user in records
    ]


@router.post("/{assignment_id}/submit", response_model=AssignmentSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: int,
    payload: AssignmentSubmissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только студенты могут отправлять решения")
    assignment = get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
    try:
        submission = create_submission(db, current_user.id, assignment, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return submission


@router.post("/courses/{course_id}", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_course_assignment(
    course_id: int,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    course = get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    return create_assignment(db, course, payload)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def edit_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    assignment = get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
    return update_assignment(db, assignment, payload)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignment(assignment_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    assignment = get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задание не найдено")
    delete_assignment(db, assignment)
