"""Registrasi, login, logout, dan kontrol akses berbasis peran."""
import functools
import hmac
import re
import sqlite3

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)

ROLES = ("pengajar", "siswa")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
MIN_PASSWORD_LENGTH = 8


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped


def role_required(role):
    """Batasi route hanya untuk peran tertentu (dicek di sisi server)."""

    def decorator(view):
        @functools.wraps(view)
        def wrapped(**kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            if g.user["role"] != role:
                abort(403)
            return view(**kwargs)

        return wrapped

    return decorator


def validate_registration(username, password, role, teacher_code):
    """Kembalikan pesan error, atau None jika data valid."""
    if not USERNAME_RE.match(username):
        return "Username harus 3-30 karakter: huruf, angka, atau underscore."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password minimal {MIN_PASSWORD_LENGTH} karakter."
    if role not in ROLES:
        return "Peran tidak valid."
    if role == "pengajar":
        expected = current_app.config.get("TEACHER_CODE")
        if not expected:
            return "Pendaftaran pengajar sedang ditutup."
        if not hmac.compare_digest(teacher_code, expected):
            return "Kode pengajar salah."
    return None


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        teacher_code = request.form.get("teacher_code", "")

        error = validate_registration(username, password, role, teacher_code)
        if error is None:
            database = get_db()
            try:
                database.execute(
                    "INSERT INTO users (username, password_hash, role) "
                    "VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), role),
                )
                database.commit()
            except sqlite3.IntegrityError:
                error = "Username sudah dipakai."
            else:
                flash("Registrasi berhasil. Silakan masuk.", "success")
                return redirect(url_for("auth.login"))

        flash(error, "error")
    return render_template("register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Username atau password salah.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("tasks.index"))
    return render_template("login.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
