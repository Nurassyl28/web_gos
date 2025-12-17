from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Импорты моделей необходимы, чтобы Alembic обнаруживал их
from app.models import course, enrollment, material, user  # noqa: F401
