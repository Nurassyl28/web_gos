from pydantic import BaseModel, Field, HttpUrl
from typing import Literal


class MaterialCreate(BaseModel):

    title: str = Field(..., min_length=3, max_length=200)
    link: HttpUrl
    material_type: Literal["video", "pdf", "link"]


class MaterialResponse(BaseModel):
    class Config:
        orm_mode = True

    id: int
    course_id: int
    title: str
    link: HttpUrl
    material_type: Literal["video", "pdf", "link"]
