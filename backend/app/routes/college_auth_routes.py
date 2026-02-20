"""
Deprecated legacy college/personnel auth routes.

These endpoints are intentionally JSON-only and return deprecation messages.
Use JSON API endpoints instead.
"""

from flask import Blueprint, jsonify


college_auth_routes = Blueprint("college_auth", __name__)


def _deprecated(message):
    return jsonify({
        "success": False,
        "message": message,
        "use": {
            "college_login": "/api/college-auth/login",
            "college_signup": "/api/college-auth/signup",
            "personnel_email_validation": "/api/auth/validate-email",
            "personnel_login_signup": "/api/auth/login and /api/auth/signup"
        }
    }), 410


@college_auth_routes.route("/login/college", methods=["GET", "POST"])
def college_login():
    return _deprecated("Legacy college login route is deprecated. Use /api/college-auth/login.")


@college_auth_routes.route("/signup/college", methods=["GET", "POST"])
def college_signup():
    return _deprecated("Legacy college signup route is deprecated. Use /api/college-auth/signup.")


@college_auth_routes.route("/logout/college")
def college_logout():
    return _deprecated("Legacy college logout route is deprecated. Use client-side token removal.")


@college_auth_routes.route("/login/personnel", methods=["GET", "POST"])
def personnel_login():
    return _deprecated("Legacy personnel login route is deprecated. Use /api/auth/login.")


@college_auth_routes.route("/signup/personnel/<int:college_id>", methods=["GET", "POST"])
def personnel_signup(college_id):
    return _deprecated("Legacy personnel signup route is deprecated. Use /api/auth/signup.")


@college_auth_routes.route("/logout/personnel")
def personnel_logout():
    return _deprecated("Legacy personnel logout route is deprecated. Use client-side token removal.")
