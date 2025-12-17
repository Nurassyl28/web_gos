from datetime import datetime

from pydantic import BaseModel


class EnrollmentResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime
