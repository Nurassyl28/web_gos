from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class AssignmentSubmissionBase(BaseModel):
    message: str = Field(..., min_length=5, max_length=2000)
    link: HttpUrl | None = Field(None, description="Ссылка на выполненное задание")


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass


class AssignmentSubmissionResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    assignment_id: int
    user_id: int
    message: str
    link: str | None
    submitted_at: datetime


class AssignmentSubmissionOverview(BaseModel):
    submission_id: int
    assignment_id: int
    assignment_title: str
    course_id: int
    course_title: str | None
    student_id: int
    student_email: str
    message: str
    link: str | None
    submitted_at: datetime
