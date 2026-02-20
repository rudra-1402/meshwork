"""
Unified Authentication Routes

Single endpoint for all student and personnel authentication.
"""

from flask import Blueprint, request, jsonify
from app.services.unified_auth_service import UnifiedAuthService


unified_auth_routes = Blueprint("unified_auth", __name__, url_prefix="/api/auth")


@unified_auth_routes.route("/validate-email", methods=["POST"])
def validate_email():
    """
    Real-time email validation endpoint.
    Called when user blurs the email field.
    """
    data = request.get_json(silent=True) or {}
    email = data.get('email')

    if not email:
        return jsonify({
            'valid': False,
            'error': 'Email is required'
        }), 400
    
    result = UnifiedAuthService.validate_email_realtime(email)
    
    if result['valid']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@unified_auth_routes.route("/login", methods=["POST"])
def unified_login():
    """
    Unified login endpoint for both students and personnel.
    """
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Email and password are required'
        }), 400
    
    result = UnifiedAuthService.unified_login(email, password)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@unified_auth_routes.route("/signup", methods=["POST"])
def unified_signup():
    """
    Unified signup endpoint for both students and personnel.
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_base_fields = ['email', 'password', 'first_name', 'last_name', 'user_type', 'college_id']
    
    for field in required_base_fields:
        if field not in data or not data[field]:
            return jsonify({
                'success': False,
                'message': f'{field} is required'
            }), 400
    
    # Validate type-specific fields
    if data['user_type'] == 'student':
        if 'username' not in data or not data['username']:
            return jsonify({
                'success': False,
                'message': 'Username is required for students'
            }), 400
    elif data['user_type'] == 'personnel':
        if 'role' not in data or not data['role']:
            return jsonify({
                'success': False,
                'message': 'Role is required for personnel'
            }), 400
    
    result = UnifiedAuthService.unified_signup(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@unified_auth_routes.route("/check-username", methods=["POST"])
def check_username():
    """
    Check if username is available.
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    
    if not username:
        return jsonify({
            'available': False,
            'error': 'Username required'
        }), 400
    
    from app.services.email_validation_service import EmailValidationService
    result = EmailValidationService.check_username_availability(username)
    
    return jsonify(result), 200
