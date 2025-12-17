from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from main import app
from app.models.user import UserRole, User
from app.schemas.user import UserCreate
from app.services.user_service import create_user

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, future=True
)


@pytest.fixture(scope="session")
def connection() -> Generator[Connection, None, None]:
    conn = engine.connect()
    trans = conn.begin()
    try:
        yield conn
    finally:
        trans.rollback()
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def initialize_database(connection: Connection) -> Generator[None, None, None]:
    Base.metadata.create_all(bind=connection)
    yield
    Base.metadata.drop_all(bind=connection)


@pytest.fixture
def db_session(connection: Connection) -> Generator[Session, None, None]:
    nested = connection.begin_nested()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        nested.rollback()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def admin_user(db_session: sessionmaker) -> User:
    user_data = UserCreate(email="admin@example.com", password="safe_pass123", full_name="Admin")
    user = create_user(db_session, user_data, role=UserRole.admin)
    return user


@pytest.fixture
def student_user(db_session: sessionmaker) -> User:
    user_data = UserCreate(email="student@example.com", password="safe_pass123", full_name="Student")
    return create_user(db_session, user_data)


@pytest.fixture
def auth_headers_admin(client: TestClient, admin_user: User) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "safe_pass123"})
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_student(client: TestClient, student_user: User) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": "student@example.com", "password": "safe_pass123"})
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
