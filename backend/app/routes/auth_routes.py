"""
Deprecated legacy auth routes.

These endpoints are intentionally JSON-only and return deprecation messages.
Use unified JSON API endpoints under /api/auth.
"""

from flask import Blueprint, jsonify


auth_routes = Blueprint("auth", __name__)


def _deprecated(message):
    return jsonify({
        "success": False,
        "message": message,
        "use": {
            "validate_email": "/api/auth/validate-email",
            "login": "/api/auth/login",
            "signup": "/api/auth/signup",
            "check_username": "/api/auth/check-username",
        }
    }), 410


@auth_routes.route("/login/user", methods=["GET", "POST"])
def user_login():
    return _deprecated("Legacy auth route is deprecated. Use /api/auth/login.")


@auth_routes.route("/signup/user", methods=["GET", "POST"])
def user_signup():
    return _deprecated("Legacy auth route is deprecated. Use /api/auth/signup.")


@auth_routes.route("/logout")
def logout():
    return _deprecated("Legacy logout route is deprecated. Use client-side token removal.")
