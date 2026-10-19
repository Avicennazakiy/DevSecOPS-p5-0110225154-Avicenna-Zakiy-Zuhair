"""Perlindungan CSRF dan header keamanan HTTP."""
import hmac
import secrets

from flask import abort, current_app, request, session

UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def protect_csrf():
    if request.method in UNSAFE_METHODS:
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")

        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, description="Token CSRF tidak valid.")


def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'"
    )
    return response


def init_app(app):
    app.before_request(protect_csrf)
    app.after_request(add_security_headers)
    app.jinja_env.globals["csrf_token"] = csrf_token
