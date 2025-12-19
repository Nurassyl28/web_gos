import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import assignments, auth, courses, enrollments, materials, users
from app.core.config import settings
from app.middleware.security import (
    HTTPSRedirectMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.project_name)

origins = settings.cors_origins or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(assignments.router)
app.include_router(enrollments.router)
app.include_router(materials.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def ping() -> dict[str, str]:
    return {"detail": "LMS Lite is running"}
