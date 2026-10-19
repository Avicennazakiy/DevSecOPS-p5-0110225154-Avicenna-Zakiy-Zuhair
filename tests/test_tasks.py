from .conftest import csrf_token, login, register


def login_as_teacher(client, username="teacher"):
    register(client, username, role="pengajar", teacher_code="TEACHER123")
    login(client, username)


def login_as_student(client, username="student"):
    register(client, username, role="siswa")
    login(client, username)


def create_task(client, title="Tugas 1", instructions="Kerjakan latihan"):
    token = csrf_token(client, "/tasks/new")
    return client.post(
        "/tasks/new",
        data={
            "csrf_token": token,
            "title": title,
            "instructions": instructions,
        },
        follow_redirects=True,
    )


def test_index_redirects_anonymous_user(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_redirects_logged_in_user(client):
    register(client, "indexuser")
    login(client, "indexuser")
    response = client.get("/")
    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]


def test_teacher_can_create_and_list_task(client):
    login_as_teacher(client)
    response = create_task(client)
    assert b"Tugas berhasil ditambahkan" in response.data
    assert b"Tugas 1" in response.data


def test_new_task_rejects_empty_and_oversized_data(client):
    login_as_teacher(client, "teacher2")

    response = create_task(client, title="", instructions="Valid")
    assert b"Judul wajib diisi" in response.data

    response = create_task(client, title="Valid", instructions="")
    assert b"Instruksi wajib diisi" in response.data

    response = create_task(client, title="x" * 101, instructions="Valid")
    assert b"Judul wajib diisi" in response.data

    response = create_task(client, title="Valid", instructions="x" * 2001)
    assert b"Instruksi wajib diisi" in response.data


def test_teacher_can_view_students(client):
    login_as_teacher(client, "teacher3")
    register(client, "student3")
    response = client.get("/students")
    assert response.status_code == 200
    assert b"student3" in response.data


def test_teacher_can_delete_own_task(client):
    login_as_teacher(client, "teacher4")
    create_task(client, "Delete me")
    response = client.post(
        "/tasks/1/delete",
        data={"csrf_token": csrf_token(client, "/tasks")},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Delete me" not in response.data


def test_teacher_cannot_delete_other_teachers_task(client):
    login_as_teacher(client, "teacher5")
    create_task(client, "Protected")
    # Switch to another teacher.
    from .conftest import login
    login(client, "teacher5")
    register(client, "teacher6", role="pengajar", teacher_code="TEACHER123")
    login(client, "teacher6")
    response = client.post(
        "/tasks/1/delete",
        data={"csrf_token": csrf_token(client, "/tasks")},
    )
    assert response.status_code == 403


def test_delete_unknown_task_returns_404(client):
    login_as_teacher(client, "teacher7")
    response = client.post(
        "/tasks/999/delete",
        data={"csrf_token": csrf_token(client, "/tasks")},
    )
    assert response.status_code == 404


def test_student_can_accept_task_and_duplicate_is_ignored(client):
    login_as_teacher(client, "teacher8")
    create_task(client, "Read chapter")
    # Registering while logged in is allowed by this application.
    register(client, "student8")
    login(client, "student8")
    response = client.get("/tasks")
    assert b"Read chapter" in response.data

    token = csrf_token(client, "/tasks")
    response = client.post(
        "/tasks/1/accept",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    assert b"Tugas ditandai selesai" in response.data
    assert b"Sudah selesai" in response.data

    token = csrf_token(client, "/tasks")
    response = client.post(
        "/tasks/1/accept",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_accept_unknown_task_returns_404(client):
    login_as_student(client, "student9")
    response = client.post(
        "/tasks/999/accept",
        data={"csrf_token": csrf_token(client, "/tasks")},
    )
    assert response.status_code == 404


def test_role_restrictions(client):
    login_as_student(client, "student10")

    response = client.get("/students")
    assert response.status_code == 403

    response = client.get("/tasks/new")
    assert response.status_code == 403

    token = csrf_token(client, "/tasks")
    response = client.post(
        "/tasks/1/accept",
        data={"csrf_token": token},
    )
    assert response.status_code == 404


def test_teacher_cannot_accept_student_task(client):
    login_as_teacher(client, "teacher11")
    create_task(client, "Teacher task")
    token = csrf_token(client, "/tasks")
    response = client.post(
        "/tasks/1/accept",
        data={"csrf_token": token},
    )
    assert response.status_code == 403
