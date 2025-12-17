from pydantic import BaseModel

from app.schemas.course import CourseResponse


class PaginatedCourses(BaseModel):
    class Config:
        orm_mode = True

    items: list[CourseResponse]
    total: int
    skip: int
    limit: int
