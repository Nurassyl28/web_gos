from datetime import datetime, timedelta
from http import HTTPStatus


def test_create_user(db_session):
    from app.schemas.user import UserCreate
    from app.services.user_service import create_user

    payload = UserCreate(email="new@example.com", password="strongpw123", full_name="New")
    user = create_user(db_session, payload)
    assert user.hashed_password != payload.password


def test_login(client, admin_user):
    response = client.post("/auth/login", json={"email": "admin@example.com", "password": "safe_pass123"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "access_token" in data

    bad = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert bad.status_code == HTTPStatus.UNAUTHORIZED


def test_register_student(client):
    payload = {"email": "newstudent@example.com", "password": "safe_pass123", "full_name": "Newbie"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "student"


def test_create_course_admin(client, auth_headers_admin):
    payload = {
        "title": "New Course",
        "description": "Desc",
        "level": "intermediate",
        "duration_minutes": 120,
    }
    response = client.post("/courses", json=payload, headers=auth_headers_admin)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["title"] == payload["title"]
    assert response.json()["level"] == "intermediate"
    assert response.json()["duration_minutes"] == 120


def test_create_course_student_forbidden(client, auth_headers_student):
    payload = {"title": "Student Course", "description": "Desc"}
    response = client.post("/courses", json=payload, headers=auth_headers_student)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_course_levels_endpoint(client):
    response = client.get("/courses/levels")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert any(item["value"] == "beginner" for item in data)


def test_enroll_duplicate(client, auth_headers_admin, auth_headers_student):
    payload = {"title": "Enroll Course", "description": "x"}
    course = client.post("/courses", json=payload, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    resp = client.post(f"/courses/{course['id']}/enroll", headers=auth_headers_student)
    assert resp.status_code == HTTPStatus.CREATED
    duplicate = client.post(f"/courses/{course['id']}/enroll", headers=auth_headers_student)
    assert duplicate.status_code == HTTPStatus.CONFLICT


def test_get_materials_unauthorized_student(client, auth_headers_admin, auth_headers_student):
    payload = {"title": "Material Course", "description": "desc"}
    course = client.post("/courses", json=payload, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    response = client.get(f"/courses/{course['id']}/materials", headers=auth_headers_student)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_courses_published_only_for_student(client, auth_headers_admin, auth_headers_student):
    course_a = client.post("/courses", json={"title": "Public", "description": "A"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course_a['id']}", json={"is_published": True}, headers=auth_headers_admin)
    course_b = client.post("/courses", json={"title": "Draft", "description": "B"}, headers=auth_headers_admin).json()
    response = client.get("/courses", headers=auth_headers_student)
    assert response.status_code == HTTPStatus.OK
    items = response.json()["items"]
    assert any(item["id"] == course_a["id"] for item in items)
    assert all(item["is_published"] for item in items)


def test_refresh_and_logout(client):
    payload = {"email": "refresh@example.com", "password": "safe_pass123"}
    client.post("/auth/register", json={**payload, "full_name": "Refresh"})
    login_resp = client.post("/auth/login", json=payload)
    assert login_resp.status_code == HTTPStatus.OK
    data = login_resp.json()
    refresh = data["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == HTTPStatus.OK
    refreshed_data = refreshed.json()
    assert refreshed_data["access_token"]

    logout_resp = client.post("/auth/logout", json={"refresh_token": refreshed_data["refresh_token"]})
    assert logout_resp.status_code == HTTPStatus.OK
    blocked = client.post("/auth/refresh", json={"refresh_token": refreshed_data["refresh_token"]})
    assert blocked.status_code == HTTPStatus.UNAUTHORIZED


def test_create_assignment_admin(client, auth_headers_admin):
    course = client.post("/courses", json={"title": "Assignment Course", "description": "Work"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    due = (datetime.utcnow() + timedelta(days=3)).isoformat()
    payload = {
        "title": "Домашка 1",
        "description": "Решите задачи",
        "link": "https://example.com/task",
        "due_date": due,
    }
    response = client.post(f"/assignments/courses/{course['id']}", json=payload, headers=auth_headers_admin)
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["link"] == payload["link"]


def test_student_sees_assignments_after_enroll(client, auth_headers_admin, auth_headers_student):
    course = client.post("/courses", json={"title": "Assignment Course 2", "description": "Work"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    client.post(f"/courses/{course['id']}/enroll", headers=auth_headers_student)
    due = (datetime.utcnow() + timedelta(days=5)).isoformat()
    client.post(
        f"/assignments/courses/{course['id']}",
        json={
            "title": "Домашка 2",
            "description": "Опис",
            "link": "https://example.com/lesson",
            "due_date": due,
        },
        headers=auth_headers_admin,
    )
    response = client.get("/assignments", headers=auth_headers_student)
    assert response.status_code == HTTPStatus.OK
    assert any(item["course_id"] == course["id"] for item in response.json())


def test_course_assignments_require_enrollment(client, auth_headers_student, auth_headers_admin):
    course = client.post("/courses", json={"title": "Secluded", "description": "Work"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    response = client.get(f"/assignments/courses/{course['id']}", headers=auth_headers_student)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_student_can_submit_assignment(client, auth_headers_admin, auth_headers_student):
    course = client.post("/courses", json={"title": "Submit Course", "description": "Work"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    client.post(f"/courses/{course['id']}/enroll", headers=auth_headers_student)
    due = (datetime.utcnow() + timedelta(days=2)).isoformat()
    assignment = client.post(
        f"/assignments/courses/{course['id']}",
        json={
            "title": "Домашка Submit",
            "description": "Отправьте отчет",
            "link": "https://example.org/task",
            "due_date": due,
        },
        headers=auth_headers_admin,
    ).json()
    payload = {"message": "Готово, см. ссылку", "link": "https://example.org/answer"}
    response = client.post(f"/assignments/{assignment['id']}/submit", json=payload, headers=auth_headers_student)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["assignment_id"] == assignment["id"]


def test_admin_can_list_submissions(client, auth_headers_admin, auth_headers_student):
    course = client.post("/courses", json={"title": "Report Course", "description": "Team"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    client.post(f"/courses/{course['id']}/enroll", headers=auth_headers_student)
    assignment = client.post(
        f"/assignments/courses/{course['id']}",
        json={
            "title": "Задание",
            "description": "Submit",
        },
        headers=auth_headers_admin,
    ).json()
    payload = {"message": "Готово"}
    client.post(f"/assignments/{assignment['id']}/submit", json=payload, headers=auth_headers_student)
    response = client.get(f"/assignments/{assignment['id']}/submissions", headers=auth_headers_admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json()


def test_submission_requires_enrollment(client, auth_headers_admin, auth_headers_student):
    course = client.post("/courses", json={"title": "Blocked Course", "description": "Hidden"}, headers=auth_headers_admin).json()
    client.put(f"/courses/{course['id']}", json={"is_published": True}, headers=auth_headers_admin)
    assignment = client.post(f"/assignments/courses/{course['id']}", json={"title": "Shielded"}, headers=auth_headers_admin).json()
    response = client.post(f"/assignments/{assignment['id']}/submit", json={"message": "Try"}, headers=auth_headers_student)
    assert response.status_code == HTTPStatus.BAD_REQUEST
