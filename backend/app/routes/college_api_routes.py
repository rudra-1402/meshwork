"""
JSON-only College Authentication API Routes.

These endpoints are intended for SPA/API clients and do not render templates
or perform form/redirect workflows.
"""

from flask import Blueprint, jsonify, request

from app.services.college_auth_services import authenticate_college, create_college


college_api_routes = Blueprint("college_api", __name__, url_prefix="/api/college-auth")


def _json_payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@college_api_routes.route("/login", methods=["POST"])
def college_login_api():
    data = _json_payload()
    email = (data.get("email") or "").strip()
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    result = authenticate_college(email, password)
    if not result["success"]:
        return jsonify({
            "success": False,
            "message": result["message"]
        }), 401

    college = result["college"]
    return jsonify({
        "success": True,
        "message": "College logged in successfully",
        "data": {
            "college": {
                "id": college.id,
                "name": college.name,
                "email": college.email,
            },
            "dashboard_route": "/dashboard"
        }
    }), 200


@college_api_routes.route("/signup", methods=["POST"])
def college_signup_api():
    data = _json_payload()

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    city = (data.get("city") or "").strip() or None
    state = (data.get("state") or "").strip() or None

    if not name or not email or not password or not confirm_password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match"
        }), 400

    college = create_college(
        name=name,
        email=email,
        password=password,
        city=city,
        state=state,
    )

    if not college:
        return jsonify({
            "success": False,
            "message": "College already exists"
        }), 409

    return jsonify({
        "success": True,
        "message": "College account created! Please login.",
        "data": {
            "college": {
                "id": college.id,
                "name": college.name,
                "email": college.email,
                "city": college.city,
                "state": college.state,
            },
            "login_route": "/college/admin-login"
        }
    }), 201
