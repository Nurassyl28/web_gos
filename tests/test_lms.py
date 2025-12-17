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
    payload = {"title": "New Course", "description": "Desc"}
    response = client.post("/courses", json=payload, headers=auth_headers_admin)
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["title"] == payload["title"]


def test_create_course_student_forbidden(client, auth_headers_student):
    payload = {"title": "Student Course", "description": "Desc"}
    response = client.post("/courses", json=payload, headers=auth_headers_student)
    assert response.status_code == HTTPStatus.FORBIDDEN


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
