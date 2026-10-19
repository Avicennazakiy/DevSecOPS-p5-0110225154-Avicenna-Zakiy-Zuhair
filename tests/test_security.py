from .conftest import csrf_token


def test_csrf_token_is_stable_for_session(client):
    first = csrf_token(client)
    second = csrf_token(client)
    assert first == second
    assert len(first) > 20


def test_security_headers(client):
    response = client.get("/register")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_csrf_rejects_wrong_token(client):
    csrf_token(client)
    response = client.post(
        "/register",
        data={
            "csrf_token": "wrong-token",
            "username": "secureuser",
            "password": "password123",
            "role": "siswa",
        },
    )
    assert response.status_code == 400
    assert b"Token CSRF tidak valid" in response.data
