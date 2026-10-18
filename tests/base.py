"""Basis tes: membuat aplikasi dengan database sementara."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db

TEACHER_CODE = "kode-rahasia-tes"
PASSWORD = "password123"


class AppTestCase(unittest.TestCase):
    csrf_enabled = False

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "kunci-khusus-tes",
                "DATABASE": str(Path(self._tmp.name) / "test.db"),
                "TEACHER_CODE": TEACHER_CODE,
                "CSRF_ENABLED": self.csrf_enabled,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    def register(self, client, username, role="siswa", password=PASSWORD, code=None):
        if code is None:
            code = TEACHER_CODE if role == "pengajar" else ""
        return client.post(
            "/register",
            data={
                "username": username,
                "password": password,
                "role": role,
                "teacher_code": code,
            },
        )

    def login(self, client, username, password=PASSWORD):
        return client.post("/login", data={"username": username, "password": password})

    def make_user(self, username, role="siswa"):
        """Buat user baru dan kembalikan client yang sudah login."""
        client = self.app.test_client()
        self.register(client, username, role)
        self.login(client, username)
        return client

    def add_task(self, client, title="Tugas 1", instructions="Kerjakan soal 1-5."):
        return client.post(
            "/tasks/new", data={"title": title, "instructions": instructions}
        )

    def task_id(self, title):
        with self.app.app_context():
            row = get_db().execute(
                "SELECT id FROM tasks WHERE title = ?", (title,)
            ).fetchone()
        return row["id"] if row else None
