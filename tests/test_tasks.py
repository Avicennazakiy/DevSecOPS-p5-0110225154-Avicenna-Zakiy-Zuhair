from app.db import get_db
from tests.base import AppTestCase


class TeacherTaskTests(AppTestCase):
    def test_teacher_can_create_task(self):
        teacher = self.make_user("bu_ani", "pengajar")
        resp = self.add_task(teacher, "Tugas Aljabar")
        self.assertEqual(resp.status_code, 302)
        self.assertIsNotNone(self.task_id("Tugas Aljabar"))

    def test_empty_title_rejected(self):
        teacher = self.make_user("bu_ani", "pengajar")
        resp = self.add_task(teacher, title="  ", instructions="isi")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Judul wajib diisi", resp.data)

    def test_teacher_can_delete_own_task(self):
        teacher = self.make_user("bu_ani", "pengajar")
        self.add_task(teacher, "Tugas Hapus")
        task_id = self.task_id("Tugas Hapus")
        resp = teacher.post(f"/tasks/{task_id}/delete")
        self.assertEqual(resp.status_code, 302)
        self.assertIsNone(self.task_id("Tugas Hapus"))

    def test_teacher_cannot_delete_other_teachers_task(self):
        ani = self.make_user("bu_ani", "pengajar")
        budi = self.make_user("pak_budi", "pengajar")
        self.add_task(ani, "Tugas Ani")
        resp = budi.post(f"/tasks/{self.task_id('Tugas Ani')}/delete")
        self.assertEqual(resp.status_code, 403)
        self.assertIsNotNone(self.task_id("Tugas Ani"))

    def test_delete_missing_task_returns_404(self):
        teacher = self.make_user("bu_ani", "pengajar")
        self.assertEqual(teacher.post("/tasks/999/delete").status_code, 404)

    def test_teacher_sees_student_progress(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas 1")
        siswa.post(f"/tasks/{self.task_id('Tugas 1')}/accept")

        resp = teacher.get("/tasks")
        self.assertIn("Selesai: 1 dari 1 siswa".encode(), resp.data)
        resp = teacher.get("/students")
        self.assertIn(b"budi_siswa", resp.data)


class StudentTaskTests(AppTestCase):
    def test_student_cannot_create_task(self):
        siswa = self.make_user("budi_siswa", "siswa")
        resp = self.add_task(siswa, "Tugas Ilegal")
        self.assertEqual(resp.status_code, 403)
        self.assertIsNone(self.task_id("Tugas Ilegal"))

    def test_student_cannot_open_task_form(self):
        siswa = self.make_user("budi_siswa", "siswa")
        self.assertEqual(siswa.get("/tasks/new").status_code, 403)

    def test_student_cannot_delete_task(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas 1")
        resp = siswa.post(f"/tasks/{self.task_id('Tugas 1')}/delete")
        self.assertEqual(resp.status_code, 403)
        self.assertIsNotNone(self.task_id("Tugas 1"))

    def test_student_cannot_see_student_list(self):
        siswa = self.make_user("budi_siswa", "siswa")
        self.assertEqual(siswa.get("/students").status_code, 403)

    def test_student_sees_task_and_accepts_it(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas 1", "Baca bab 2.")

        resp = siswa.get("/tasks")
        self.assertIn(b"Tugas 1", resp.data)
        self.assertIn(b"Baca bab 2.", resp.data)
        self.assertIn(b"Tandai selesai", resp.data)

        siswa.post(f"/tasks/{self.task_id('Tugas 1')}/accept")
        resp = siswa.get("/tasks")
        self.assertIn(b"Sudah selesai", resp.data)
        self.assertNotIn(b"Tandai selesai", resp.data)

    def test_accept_is_idempotent(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas 1")
        task_id = self.task_id("Tugas 1")
        siswa.post(f"/tasks/{task_id}/accept")
        siswa.post(f"/tasks/{task_id}/accept")
        with self.app.app_context():
            count = get_db().execute("SELECT COUNT(*) FROM completions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_teacher_cannot_accept_task(self):
        teacher = self.make_user("bu_ani", "pengajar")
        self.add_task(teacher, "Tugas 1")
        resp = teacher.post(f"/tasks/{self.task_id('Tugas 1')}/accept")
        self.assertEqual(resp.status_code, 403)

    def test_completion_is_per_student(self):
        teacher = self.make_user("bu_ani", "pengajar")
        budi = self.make_user("budi_siswa", "siswa")
        sari = self.make_user("sari_siswa", "siswa")
        self.add_task(teacher, "Tugas 1")
        budi.post(f"/tasks/{self.task_id('Tugas 1')}/accept")
        self.assertIn(b"Tandai selesai", sari.get("/tasks").data)

    def test_deleting_task_removes_completions(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas 1")
        task_id = self.task_id("Tugas 1")
        siswa.post(f"/tasks/{task_id}/accept")
        teacher.post(f"/tasks/{task_id}/delete")
        with self.app.app_context():
            count = get_db().execute("SELECT COUNT(*) FROM completions").fetchone()[0]
        self.assertEqual(count, 0)

    def test_task_content_is_html_escaped(self):
        teacher = self.make_user("bu_ani", "pengajar")
        siswa = self.make_user("budi_siswa", "siswa")
        self.add_task(teacher, "Tugas XSS", "<script>alert(1)</script>")
        resp = siswa.get("/tasks")
        self.assertNotIn(b"<script>alert(1)</script>", resp.data)
        self.assertIn(b"&lt;script&gt;", resp.data)
