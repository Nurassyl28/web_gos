from datetime import datetime

from pydantic import BaseModel, Field

from app.models.course import CourseLevel


class CourseBase(BaseModel):

    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    level: CourseLevel = Field(
        CourseLevel.beginner,
        description="Уровень сложности курса",
    )
    duration_minutes: int | None = Field(
        None,
        ge=5,
        description="Примерная продолжительность курса в минутах",
    )


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):

    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_published: bool | None = None
    level: CourseLevel | None = Field(
        None,
        description="Обновляемый уровень сложности курса",
    )
    duration_minutes: int | None = Field(
        None,
        ge=5,
        description="Обновляемая продолжительность курса в минутах",
    )


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
    level: CourseLevel
    duration_minutes: int | None


class CourseLevelInfo(BaseModel):
    value: CourseLevel
    label: str
    description: str


COURSE_LEVELS: list[CourseLevelInfo] = [
    CourseLevelInfo(
        value=CourseLevel.beginner,
        label="Начинающий уровень",
        description="Для тех, кто только знакомится с предметом.",
    ),
    CourseLevelInfo(
        value=CourseLevel.intermediate,
        label="Средний уровень",
        description="Подходит для студентов с базовыми знаниями.",
    ),
    CourseLevelInfo(
        value=CourseLevel.advanced,
        label="Продвинутый уровень",
        description="Трудные темы и задачи для опытных учеников.",
    ),
]
