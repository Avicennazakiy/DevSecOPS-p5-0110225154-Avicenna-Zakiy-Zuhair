from app.db import get_db
from tests.base import PASSWORD, AppTestCase, TEACHER_CODE


class RegisterTests(AppTestCase):
    def test_register_siswa_success(self):
        resp = self.register(self.client, "budi_siswa")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/login"))

    def test_register_pengajar_with_valid_code(self):
        resp = self.register(self.client, "bu_ani", role="pengajar")
        self.assertEqual(resp.status_code, 302)

    def test_register_pengajar_with_wrong_code_rejected(self):
        resp = self.register(self.client, "palsu", role="pengajar", code="salah")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Kode pengajar salah", resp.data)
        with self.app.app_context():
            count = get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertEqual(count, 0)

    def test_register_pengajar_closed_when_code_not_configured(self):
        self.app.config["TEACHER_CODE"] = None
        resp = self.register(self.client, "bu_ani", role="pengajar", code="apa-saja")
        self.assertIn(b"ditutup", resp.data)

    def test_register_rejects_short_password(self):
        resp = self.register(self.client, "budi_siswa", password="pendek")
        self.assertIn(b"minimal 8 karakter", resp.data)

    def test_register_rejects_invalid_username(self):
        resp = self.register(self.client, "a b!")
        self.assertIn(b"Username harus", resp.data)

    def test_register_rejects_unknown_role(self):
        resp = self.register(self.client, "budi_siswa", role="admin")
        self.assertIn(b"Peran tidak valid", resp.data)

    def test_register_duplicate_username_case_insensitive(self):
        self.register(self.client, "Budi_Siswa")
        resp = self.register(self.client, "budi_siswa")
        self.assertIn(b"sudah dipakai", resp.data)

    def test_password_is_stored_hashed(self):
        self.register(self.client, "budi_siswa")
        with self.app.app_context():
            row = get_db().execute(
                "SELECT password_hash FROM users WHERE username = ?",
                ("budi_siswa",),
            ).fetchone()
        self.assertNotEqual(row["password_hash"], PASSWORD)
        self.assertNotIn(PASSWORD, row["password_hash"])


class LoginTests(AppTestCase):
    def test_login_success_redirects_to_tasks(self):
        self.register(self.client, "budi_siswa")
        resp = self.login(self.client, "budi_siswa")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/"))

    def test_login_wrong_password(self):
        self.register(self.client, "budi_siswa")
        resp = self.login(self.client, "budi_siswa", password="salahsalah")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Username atau password salah", resp.data)

    def test_login_unknown_user_gives_same_message(self):
        resp = self.login(self.client, "tidak_ada")
        self.assertIn(b"Username atau password salah", resp.data)

    def test_sql_injection_attempt_does_not_log_in(self):
        self.register(self.client, "budi_siswa")
        resp = self.client.post(
            "/login", data={"username": "' OR '1'='1' --", "password": "x"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Username atau password salah", resp.data)

    def test_logout_clears_session(self):
        client = self.make_user("budi_siswa")
        client.post("/logout")
        resp = client.get("/tasks")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/login"))

    def test_tasks_page_requires_login(self):
        resp = self.client.get("/tasks")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers["Location"].endswith("/login"))


class SecurityTests(AppTestCase):
    csrf_enabled = True

    def test_post_without_csrf_token_is_rejected(self):
        resp = self.client.post("/login", data={"username": "a", "password": "b"})
        self.assertEqual(resp.status_code, 400)

    def test_security_headers_present(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.headers["X-Frame-Options"], "DENY")
        self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", resp.headers["Content-Security-Policy"])

    def test_teacher_code_constant_is_not_exposed_in_pages(self):
        resp = self.client.get("/register")
        self.assertNotIn(TEACHER_CODE.encode(), resp.data)
