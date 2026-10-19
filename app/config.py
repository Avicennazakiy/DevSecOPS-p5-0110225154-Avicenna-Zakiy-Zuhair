"""Konfigurasi aplikasi. Nilai sensitif dibaca dari environment variable."""
import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    DATABASE = os.environ.get("DATABASE_PATH")

    
    TEACHER_CODE = os.environ.get("TEACHER_CODE")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 64 * 1024
