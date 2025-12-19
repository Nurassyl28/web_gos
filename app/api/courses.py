from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user_optional
from app.db.session import get_db
from app.models.enrollment import Enrollment
from app.models.user import UserRole
from app.schemas.course import (
    COURSE_LEVELS,
    CourseCreate,
    CourseLevelInfo,
    CourseResponse,
    CourseUpdate,
)
from app.schemas.pagination import PaginatedCourses
from app.services.course_service import (
    create_course,
    delete_course,
    get_course,
    list_courses,
    update_course,
)
from app.utils.exceptions import client_error

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/", response_model=PaginatedCourses)
def read_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    is_published: bool | None = None,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    is_admin = current_user and current_user.role == UserRole.admin
    published_only = not is_admin
    filters_published = is_published if is_admin else None
    items, total = list_courses(
        db,
        skip=skip,
        limit=limit,
        search=search,
        published_only=published_only,
        is_published=filters_published,
    )
    return PaginatedCourses(
        items=[
            CourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                is_published=course.is_published,
                created_by=course.created_by,
                created_at=course.created_at,
                students_count=count,
                level=course.level,
                duration_minutes=course.duration_minutes,
            )
            for course, count in items
        ],
        total=total,
        skip=skip,
        limit=min(limit, 100),
    )


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_new_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    course = create_course(db, payload, current_admin.id)
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        is_published=course.is_published,
        created_by=course.created_by,
        created_at=course.created_at,
        students_count=0,
        level=course.level,
        duration_minutes=course.duration_minutes,
    )


@router.put("/{course_id}", response_model=CourseResponse)
def edit_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    course = get_course(db, course_id)
    if course is None:
        raise client_error("COURSE_NOT_FOUND", "Курс не найден", status_code=404)
    course = update_course(db, course, payload)
    students_count = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course.id)
        .scalar()
        or 0
    )
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        is_published=course.is_published,
        created_by=course.created_by,
        created_at=course.created_at,
        students_count=students_count,
        level=course.level,
        duration_minutes=course.duration_minutes,
    )


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    course = get_course(db, course_id)
    if course is None:
        raise client_error("COURSE_NOT_FOUND", "Курс не найден", status_code=404)
    delete_course(db, course)


@router.get("/{course_id}", response_model=CourseResponse)
def read_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    course = get_course(db, course_id)
    if course is None:
        raise client_error("COURSE_NOT_FOUND", "Курс не найден", status_code=404)
    if not course.is_published and (not current_user or current_user.role != UserRole.admin):
        raise client_error("COURSE_NOT_FOUND", "Курс не найден", status_code=404)
    students_count = (
        db.query(func.count(Enrollment.id))
        .filter(Enrollment.course_id == course.id)
        .scalar()
        or 0
    )
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        is_published=course.is_published,
        created_by=course.created_by,
        created_at=course.created_at,
        students_count=students_count,
        level=course.level,
        duration_minutes=course.duration_minutes,
    )


@router.get("/levels", response_model=list[CourseLevelInfo])
def read_course_levels():
    return COURSE_LEVELS
