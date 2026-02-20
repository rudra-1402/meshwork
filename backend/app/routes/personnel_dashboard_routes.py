"""
Personnel Dashboard Routes

Routes for college personnel (HOD, faculty, staff) to manage students and college operations.
All responses are JSON only — no SSR templates.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.services.college_personnel_services import get_personnel_by_id
from app.services.whitelist_service import WhitelistService
from app.services.college_auth_services import (
    get_college_email_configuration,
    update_college_email_configuration,
)
from app.models.user import User
from app.models.whitelisted_email import WhitelistedEmail
from functools import wraps

_ALLOWED_CSV_MIME_TYPES = {'text/csv', 'application/csv', 'application/vnd.ms-excel'}
_MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB


personnel_dashboard_routes = Blueprint("personnel", __name__)


# ===== HELPER DECORATORS =====

def personnel_required(f):
    """Decorator to ensure user is authenticated personnel"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        identity = get_jwt_identity()

        if not identity or not str(identity).startswith('personnel_'):
            return jsonify({"success": False, "message": "Access denied. Personnel login required."}), 403

        personnel_id = int(str(identity).replace('personnel_', ''))
        personnel = get_personnel_by_id(personnel_id)

        if not personnel or not personnel.is_active:
            return jsonify({"success": False, "message": "Invalid or inactive personnel account."}), 403

        return f(personnel=personnel, *args, **kwargs)

    return decorated_function


def can_manage_students_required(f):
    """Decorator to ensure personnel can manage students"""
    @wraps(f)
    @personnel_required
    def decorated_function(personnel=None, *args, **kwargs):
        if not personnel.can_manage_students:
            return jsonify({"success": False, "message": "You don't have permission to manage students."}), 403

        return f(personnel=personnel, *args, **kwargs)

    return decorated_function


def can_manage_personnel_required(f):
    """Decorator to ensure personnel can manage college/personnel settings"""
    @wraps(f)
    @personnel_required
    def decorated_function(personnel=None, *args, **kwargs):
        if not personnel.can_manage_personnel:
            return jsonify({"success": False, "message": "You don't have permission to manage college settings."}), 403

        return f(personnel=personnel, *args, **kwargs)

    return decorated_function


# ===== ROUTES =====

@personnel_dashboard_routes.route("/dashboard")
@personnel_required
def personnel_dashboard(personnel=None):
    """Personnel main dashboard"""
    whitelist_stats = WhitelistService.get_whitelist_stats(personnel.college_id)

    recent_whitelist = WhitelistService.get_college_whitelist(
        personnel.college_id,
        include_registered=True
    )[:10]

    return jsonify({
        "success": True,
        "personnel": {
            "id": personnel.id,
            "first_name": personnel.first_name,
            "last_name": personnel.last_name,
            "email": personnel.email,
            "role": personnel.role,
            "college_id": personnel.college_id,
        },
        "stats": whitelist_stats,
        "recent_whitelist": [
            {
                "id": e.id,
                "email": e.email,
                "is_registered": e.is_registered,
            }
            for e in recent_whitelist
        ]
    }), 200


@personnel_dashboard_routes.route("/students")
@personnel_required
def view_students(personnel=None):
    """View all students in college"""
    students = User.query.filter_by(college_id=personnel.college_id).all()

    return jsonify({
        "success": True,
        "students": [
            {
                "id": s.id,
                "username": s.username,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.email,
                "xp": s.xp,
                "level": s.level,
            }
            for s in students
        ]
    }), 200


@personnel_dashboard_routes.route("/whitelist")
@can_manage_students_required
def manage_whitelist(personnel=None):
    """Manage student email whitelist"""
    include_registered = request.args.get('include_registered', 'true').lower() == 'true'

    whitelist = WhitelistService.get_college_whitelist(
        personnel.college_id,
        include_registered=include_registered
    )

    stats = WhitelistService.get_whitelist_stats(personnel.college_id)

    return jsonify({
        "success": True,
        "whitelist": [
            {
                "id": e.id,
                "email": e.email,
                "student_name": getattr(e, 'student_name', None),
                "is_registered": e.is_registered,
            }
            for e in whitelist
        ],
        "stats": stats
    }), 200


@personnel_dashboard_routes.route("/whitelist/add-single", methods=["POST"])
@can_manage_students_required
def add_student_email(personnel=None):
    """Add single student email to whitelist"""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    enrollment = data.get("enrollment", "").strip() or None
    name = data.get("name", "").strip() or None
    notes = data.get("notes", "").strip() or None

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    success, message, entry = WhitelistService.add_email_to_whitelist(
        college_id=personnel.college_id,
        email=email,
        added_by_personnel_id=personnel.id,
        student_enrollment=enrollment,
        student_name=name,
        notes=notes
    )

    status = 201 if success else 400
    return jsonify({"success": success, "message": message}), status


@personnel_dashboard_routes.route("/whitelist/bulk-add", methods=["POST"])
@can_manage_students_required
def bulk_add_emails(personnel=None):
    """Bulk upload student emails from CSV"""
    if 'csv_file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    file = request.files['csv_file']

    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    safe_name = secure_filename(file.filename)
    if not safe_name.lower().endswith('.csv'):
        return jsonify({"success": False, "message": "File must be a CSV (.csv extension required)."}), 400

    if file.content_type not in _ALLOWED_CSV_MIME_TYPES:
        return jsonify({"success": False, "message": "Invalid file type. Only CSV files are accepted."}), 400

    raw_bytes = file.read(_MAX_CSV_BYTES + 1)
    if len(raw_bytes) > _MAX_CSV_BYTES:
        return jsonify({"success": False, "message": "File exceeds the 5 MB size limit."}), 400

    try:
        csv_content = raw_bytes.decode('utf-8')

        result = WhitelistService.bulk_add_from_csv(
            college_id=personnel.college_id,
            csv_content=csv_content,
            added_by_personnel_id=personnel.id
        )

        return jsonify({"success": True, "results": result}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing file: {str(e)}"}), 500


@personnel_dashboard_routes.route("/whitelist/remove/<int:email_id>", methods=["POST"])
@can_manage_students_required
def remove_email(personnel=None, email_id=None):
    """Remove email from whitelist — only for entries belonging to this personnel's college."""
    from app.extensions import db

    entry = db.session.get(WhitelistedEmail, email_id)

    if not entry:
        return jsonify({"success": False, "message": "Whitelist entry not found."}), 404

    if entry.college_id != personnel.college_id:
        return jsonify({"success": False, "message": "Access denied. You can only remove entries for your own college."}), 403

    success, message = WhitelistService.remove_from_whitelist(email_id)

    status = 200 if success else 400
    return jsonify({"success": success, "message": message}), status


@personnel_dashboard_routes.route("/profile")
@personnel_required
def personnel_profile(personnel=None):
    """Personnel profile"""
    return jsonify({
        "success": True,
        "personnel": {
            "id": personnel.id,
            "first_name": personnel.first_name,
            "last_name": personnel.last_name,
            "email": personnel.email,
            "role": personnel.role,
            "college_id": personnel.college_id,
            "can_manage_students": personnel.can_manage_students,
        }
    }), 200


@personnel_dashboard_routes.route("/college/email-config", methods=["GET"])
@can_manage_personnel_required
def get_college_email_config(personnel=None):
    """Get current college domain and email-pattern configuration."""
    success, message, data = get_college_email_configuration(personnel.college_id)
    if not success:
        return jsonify({"success": False, "message": message}), 404

    return jsonify({
        "success": True,
        "message": "College email configuration fetched successfully",
        "data": data,
    }), 200


@personnel_dashboard_routes.route("/college/email-config", methods=["PATCH"])
@can_manage_personnel_required
def set_college_email_config(personnel=None):
    """
    Set college domain and email patterns.

    Expects JSON body:
    {
      "domain": "mitindia.edu",
      "student_email_pattern": "{enrollment}@mitindia.edu",
      "personnel_email_pattern": "{personnel_id}-{role}@mitindia.edu"
    }
    """
    payload = request.get_json(silent=True) or {}
    domain = payload.get("domain")
    student_email_pattern = payload.get("student_email_pattern")
    personnel_email_pattern = payload.get("personnel_email_pattern")

    if not domain or not student_email_pattern or not personnel_email_pattern:
        return jsonify({
            "success": False,
            "message": "domain, student_email_pattern, and personnel_email_pattern are required",
        }), 400

    success, message, data = update_college_email_configuration(
        college_id=personnel.college_id,
        domain=domain,
        student_email_pattern=student_email_pattern,
        personnel_email_pattern=personnel_email_pattern,
    )

    if not success:
        status = 409 if message == "Domain is already assigned to another college" else 400
        return jsonify({"success": False, "message": message}), status

    return jsonify({
        "success": True,
        "message": "College email configuration updated successfully",
        "data": data,
    }), 200
