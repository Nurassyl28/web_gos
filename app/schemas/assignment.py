from datetime import datetime, timezone

from pydantic import BaseModel, Field, HttpUrl, root_validator


class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    link: HttpUrl | None = Field(None, description="Ссылка на материал или задание")
    due_date: datetime | None = Field(None, description="Дата и время дедлайна задания")


class AssignmentCreate(AssignmentBase):
    due_date: datetime = Field(..., description="Дата и время дедлайна задания")

    @root_validator
    def ensure_not_in_past(cls, values):
        due: datetime | None = values.get("due_date")
        if due:
            now = datetime.now(timezone.utc)
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            else:
                due = due.astimezone(timezone.utc)
            if due < now:
                raise ValueError("Дедлайн не может быть в прошлом")
            values["due_date"] = due
        return values


class AssignmentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=1000)
    link: HttpUrl | None = Field(None, description="Обновлённая ссылка на материал")
    due_date: datetime | None = Field(None, description="Обновлённый дедлайн")


class AssignmentResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    course_id: int
    title: str
    description: str | None
    link: str | None
    due_date: datetime | None
    created_at: datetime
