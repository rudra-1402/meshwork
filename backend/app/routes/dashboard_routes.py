from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.college import College
from app.models.scoring import UserScoring

dashboard_routes = Blueprint("dashboard", __name__)


@dashboard_routes.route("/dashboard")
@jwt_required()
def dashboard():
    """
    User dashboard data — requires JWT authentication.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    scoring = UserScoring.query.filter_by(user_id=user_id).first()
    has_completed_questionnaire = bool(scoring) or getattr(user, 'has_completed_questionnaire', False)

    return jsonify({
        'success': True,
        'user': {
            'username': user.username,
            'email': user.email,
            'has_completed_questionnaire': has_completed_questionnaire,
            'role': 'user',
            'xp': user.xp,
            'level': user.level,
            'current_streak': user.current_streak,
            'max_streak': user.max_streak,
            'is_admin': getattr(user, 'is_admin', False),
        }
    }), 200


@dashboard_routes.route("/profile")
@jwt_required()
def profile_page():
    """
    User profile data — requires JWT authentication.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    scoring = UserScoring.query.filter_by(user_id=user_id).first()

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'xp': user.xp,
            'level': user.level,
            'current_streak': user.current_streak,
            'max_streak': user.max_streak,
        },
        'has_scoring': bool(scoring),
    }), 200


@dashboard_routes.route("/dashboard/college")
@jwt_required()
def college_dashboard():
    """
    College dashboard data — requires JWT authentication with college identity.
    """
    identity = str(get_jwt_identity())
    if not identity.startswith("college_"):
        return jsonify({'success': False, 'message': 'College access required'}), 403

    try:
        college_id = int(identity.replace("college_", "", 1))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    college = db.session.get(College, college_id)
    if not college:
        return jsonify({'success': False, 'message': 'College not found'}), 404

    _MAX_PER_PAGE = 100
    page = request.args.get('page', 1, type=int) or 1
    per_page = min(request.args.get('per_page', 20, type=int) or 20, _MAX_PER_PAGE)

    pagination = (
        User.query
        .filter_by(college_id=college_id)
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        'success': True,
        'college': {
            'name': college.name,
            'email': college.email,
        },
        'user_count': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'users': [{'id': u.id, 'username': u.username} for u in pagination.items],
    }), 200
