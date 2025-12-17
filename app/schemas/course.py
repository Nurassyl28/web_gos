from datetime import datetime

from pydantic import BaseModel, Field


class CourseBase(BaseModel):

    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):

    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_published: bool | None = None


class CourseResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    title: str
    description: str | None
    is_published: bool
    created_by: int
    created_at: datetime
    students_count: int
