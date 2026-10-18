"""Manajemen tugas: pengajar menambah/menghapus, siswa melihat dan menandai selesai."""
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import login_required, role_required
from .db import get_db

bp = Blueprint("tasks", __name__)

MAX_TITLE_LENGTH = 100
MAX_INSTRUCTIONS_LENGTH = 2000


@bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login"))
    return redirect(url_for("tasks.list_tasks"))


@bp.route("/tasks")
@login_required
def list_tasks():
    database = get_db()
    total_students = database.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'siswa'"
    ).fetchone()[0]

    if g.user["role"] == "siswa":
        rows = database.execute(
            "SELECT t.id, t.title, t.instructions, t.created_at, "
            "       u.username AS teacher, "
            "       EXISTS (SELECT 1 FROM completions c "
            "               WHERE c.task_id = t.id AND c.user_id = ?) AS done "
            "FROM tasks t JOIN users u ON u.id = t.created_by "
            "ORDER BY t.id DESC",
            (g.user["id"],),
        ).fetchall()
    else:
        rows = database.execute(
            "SELECT t.id, t.title, t.instructions, t.created_at, t.created_by, "
            "       u.username AS teacher, "
            "       (SELECT COUNT(*) FROM completions c "
            "        WHERE c.task_id = t.id) AS done_count "
            "FROM tasks t JOIN users u ON u.id = t.created_by "
            "ORDER BY t.id DESC"
        ).fetchall()

    return render_template("tasks.html", tasks=rows, total_students=total_students)


@bp.route("/tasks/new", methods=("GET", "POST"))
@role_required("pengajar")
def new_task():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        instructions = request.form.get("instructions", "").strip()

        error = None
        if not title or len(title) > MAX_TITLE_LENGTH:
            error = f"Judul wajib diisi (maksimal {MAX_TITLE_LENGTH} karakter)."
        elif not instructions or len(instructions) > MAX_INSTRUCTIONS_LENGTH:
            error = (
                "Instruksi wajib diisi "
                f"(maksimal {MAX_INSTRUCTIONS_LENGTH} karakter)."
            )

        if error is None:
            database = get_db()
            database.execute(
                "INSERT INTO tasks (title, instructions, created_by) "
                "VALUES (?, ?, ?)",
                (title, instructions, g.user["id"]),
            )
            database.commit()
            flash("Tugas berhasil ditambahkan.", "success")
            return redirect(url_for("tasks.list_tasks"))
        flash(error, "error")
    return render_template("task_form.html")


@bp.route("/tasks/<int:task_id>/delete", methods=("POST",))
@role_required("pengajar")
def delete_task(task_id):
    database = get_db()
    task = database.execute(
        "SELECT id, created_by FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if task is None:
        abort(404)
    if task["created_by"] != g.user["id"]:
        abort(403)

    database.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    database.commit()
    flash("Tugas dihapus.", "success")
    return redirect(url_for("tasks.list_tasks"))


@bp.route("/tasks/<int:task_id>/accept", methods=("POST",))
@role_required("siswa")
def accept_task(task_id):
    database = get_db()
    task = database.execute(
        "SELECT id FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if task is None:
        abort(404)

    database.execute(
        "INSERT OR IGNORE INTO completions (user_id, task_id) VALUES (?, ?)",
        (g.user["id"], task_id),
    )
    database.commit()
    flash("Tugas ditandai selesai.", "success")
    return redirect(url_for("tasks.list_tasks"))


@bp.route("/students")
@role_required("pengajar")
def students():
    database = get_db()
    total_tasks = database.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    rows = database.execute(
        "SELECT u.username, u.created_at, "
        "       (SELECT COUNT(*) FROM completions c "
        "        WHERE c.user_id = u.id) AS done_count "
        "FROM users u WHERE u.role = 'siswa' ORDER BY u.username"
    ).fetchall()
    return render_template("students.html", students=rows, total_tasks=total_tasks)
