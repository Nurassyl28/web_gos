from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import auth, courses, enrollments, materials, users
from app.core.config import settings

app = FastAPI(title=settings.project_name)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(enrollments.router)
app.include_router(materials.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def ping() -> dict[str, str]:
    return {"detail": "LMS Lite is running"}
