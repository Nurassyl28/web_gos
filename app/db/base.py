from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Импорты моделей необходимы, чтобы Alembic обнаруживал их
from app.models import assignment, assignment_submission, course, enrollment, material, user  # noqa: F401
