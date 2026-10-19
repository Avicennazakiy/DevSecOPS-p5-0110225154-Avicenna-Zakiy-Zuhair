from app.auth import validate_registration

from .conftest import csrf_token, login, logout, register


def test_register_student_success(client):
    response = register(client, "student1")
    assert response.status_code == 200
    assert b"Registrasi berhasil" in response.data


def test_register_teacher_with_valid_code(client):
    response = register(
        client, "teacher1", role="pengajar", teacher_code="TEACHER123"
    )
    assert response.status_code == 200
    assert b"Registrasi berhasil" in response.data


def test_register_teacher_rejects_wrong_code(client):
    response = register(
        client, "teacher2", role="pengajar", teacher_code="WRONGCODE"
    )
    assert b"Kode pengajar salah" in response.data


def test_register_duplicate_username(client):
    register(client, "duplicate1")
    response = register(client, "duplicate1")
    assert b"Username sudah dipakai" in response.data


def test_register_rejects_invalid_form(client):
    token = csrf_token(client)
    response = client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "a",
            "password": "short",
            "role": "invalid",
        },
    )
    assert b"Username harus 3-30 karakter" in response.data


def test_validate_registration_teacher_code_configuration(app):
    with app.app_context():
        assert validate_registration(
            "teacher", "password123", "pengajar", ""
        ) == "Kode pengajar salah."
        app.config["TEACHER_CODE"] = None
        assert validate_registration(
            "teacher", "password123", "pengajar", ""
        ) == "Pendaftaran pengajar sedang ditutup."


def test_validate_registration_rejects_short_password_and_invalid_role():
    assert "Password minimal" in validate_registration(
        "validuser", "short", "siswa", ""
    )
    assert validate_registration(
        "validuser", "password123", "admin", ""
    ) == "Peran tidak valid."


def test_login_wrong_and_correct_password(client):
    register(client, "loginuser")
    response = login(client, "loginuser", "wrongpassword")
    assert b"Username atau password salah" in response.data

    response = login(client, "loginuser")
    assert b"Daftar Tugas" in response.data


def test_login_unknown_user(client):
    response = login(client, "nobody")
    assert b"Username atau password salah" in response.data


def test_logout(client):
    register(client, "logoutuser")
    login(client, "logoutuser")
    response = logout(client)
    assert response.status_code == 200
    assert b"Masuk" in response.data


def test_login_required_redirects_anonymous_user(client):
    response = client.get("/tasks")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_csrf_rejects_missing_token(client):
    response = client.post(
        "/register",
        data={"username": "badcsrf", "password": "password123", "role": "siswa"},
    )
    assert response.status_code == 400
    assert b"Token CSRF tidak valid" in response.data
