"""Konfigurasi aplikasi. Nilai sensitif dibaca dari environment variable."""
import os
import secrets


class Config:
    # Jika SECRET_KEY tidak diset, dibuat acak per proses (cukup untuk
    # pengembangan lokal; untuk produksi wajib diset lewat environment).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Lokasi file SQLite. Jika kosong, dipakai instance/lms.db.
    DATABASE = os.environ.get("DATABASE_PATH")

    # Kode undangan untuk mendaftar sebagai pengajar. Jika kosong,
    # pendaftaran pengajar ditutup.
    TEACHER_CODE = os.environ.get("TEACHER_CODE")

    CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 64 * 1024
