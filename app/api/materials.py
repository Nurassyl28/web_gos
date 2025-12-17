from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user_optional
from app.db.session import get_db
from app.models.user import UserRole
from app.schemas.material import MaterialCreate, MaterialResponse
from app.services.course_service import get_course
from app.services.enrollment_service import get_enrollment
from app.services.material_service import (
    create_material,
    delete_material,
    get_material,
    list_materials,
)

router = APIRouter(tags=["materials"])


@router.get("/courses/{course_id}/materials", response_model=list[MaterialResponse])
def read_materials(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    course = get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
    if current_user.role != UserRole.admin:
        enrollment = get_enrollment(db, current_user.id, course_id)
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
    materials = list_materials(db, course_id)
    return materials


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def add_material(
    course_id: int,
    payload: MaterialCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    course = get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    return create_material(db, course, payload)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_material(material_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    material = get_material(db, material_id)
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Материал не найден")
    delete_material(db, material)
