import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.sqlite"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(database),
            "TEACHER_CODE": "TEACHER123",
        }
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_token(client, path="/register"):
    client.get(path)
    with client.session_transaction() as session:
        return session["csrf_token"]


def register(client, username, password="password123", role="siswa", teacher_code=""):
    token = csrf_token(client)
    return client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": username,
            "password": password,
            "role": role,
            "teacher_code": teacher_code,
        },
        follow_redirects=True,
    )


def login(client, username, password="password123"):
    token = csrf_token(client, "/login")
    return client.post(
        "/login",
        data={"csrf_token": token, "username": username, "password": password},
        follow_redirects=True,
    )


def logout(client):
    token = csrf_token(client, "/tasks")
    return client.post("/logout", data={"csrf_token": token}, follow_redirects=True)
