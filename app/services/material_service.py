from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.material import Material
from app.utils.exceptions import client_error
from app.schemas.material import MaterialCreate
from app.models.course import Course


def get_material(db: Session, material_id: int) -> Material | None:
    return db.query(Material).filter(Material.id == material_id).first()


def create_material(db: Session, course: Course, payload: MaterialCreate) -> Material:
    if course is None:
        raise client_error("COURSE_NOT_FOUND", "Курс не найден", status_code=404)
    material = Material(
        course_id=course.id,
        title=payload.title,
        link=str(payload.link),
        material_type=payload.material_type,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def list_materials(db: Session, course_id: int) -> list[Material]:
    return (
        db.query(Material)
        .filter(Material.course_id == course_id)
        .order_by(Material.created_at.desc())
        .all()
    )


def delete_material(db: Session, material: Material) -> None:
    db.delete(material)
    db.commit()
