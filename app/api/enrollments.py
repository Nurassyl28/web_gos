from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.enrollment import EnrollmentResponse
from app.schemas.user import UserResponse
from app.services.course_service import get_course
from app.services.enrollment_service import (
    create_enrollment,
    list_course_students,
    list_student_enrollments,
)

router = APIRouter(tags=["enrollments"])


@router.post("/courses/{course_id}/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_step(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только студенты могут записываться")
    course = get_course(db, course_id)
    if not course or not course.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    enrollment = create_enrollment(db, current_user.id, course)
    return enrollment


@router.get("/me/enrollments", response_model=list[EnrollmentResponse])
def read_my_enrollments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return list_student_enrollments(db, current_user.id)


@router.get("/courses/{course_id}/students", response_model=list[UserResponse])
def read_course_students(course_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    course = get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    students = list_course_students(db, course_id)
    return [UserResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role.value, created_at=user.created_at) for user in students]
