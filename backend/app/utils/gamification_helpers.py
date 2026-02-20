"""
Gamification Helper Utilities

Common utilities for gamification features.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.user import User


# ===== DECORATOR: Admin Required =====
#
# The admin_required decorator was removed from this file.
# Use the canonical implementation in app/routes/admin_routes.py
# or app/utils/decorators.py for admin access control.


# ===== DECORATOR: Moderator Required =====

def moderator_required(fn):
    """
    Decorator to require moderator privileges in a community.

    Usage:
        @app.route('/community/<int:community_id>/moderate')
        @moderator_required
        def moderate_community(community_id):
            # Only moderators can access this
            pass
    """
    from flask_jwt_extended import jwt_required

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if isinstance(identity, str) and identity.startswith("personnel_"):
            return jsonify({'error': 'Access restricted to student accounts'}), 403
        if identity is None:
            return jsonify({'error': 'Authentication required'}), 401
        user_id = int(identity)
        user = db.session.get(User, user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Get community_id from kwargs only (args[0] is unreliable — see U7 fix)
        community_id = kwargs.get('community_id')
        
        if not community_id:
            return jsonify({
                'success': False,
                'error': 'Community ID required'
            }), 400
        
        # Check if user is moderator
        from app.models.community_moderator import CommunityModerator
        
        is_moderator = CommunityModerator.query.filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        
        if not is_moderator:
            return jsonify({
                'success': False,
                'error': 'Moderator privileges required'
            }), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


# ===== RESPONSE FORMATTERS =====

def success_response(data, message=None, status=200):
    """
    Format successful API response.
    
    Usage:
        return success_response({'user': user_data}, 'User created', 201)
    """
    response = {
        'success': True,
    }
    
    if message:
        response['message'] = message
    
    response.update(data)
    
    return jsonify(response), status


def error_response(message, status=400, error_code=None):
    """
    Format error API response.
    
    Usage:
        return error_response('Invalid input', 400, 'INVALID_INPUT')
    """
    response = {
        'success': False,
        'error': message
    }
    
    if error_code:
        response['error_code'] = error_code
    
    return jsonify(response), status


# ===== PAGINATION HELPER =====

def paginate_query(query, page=1, per_page=20, max_per_page=100):
    """
    Paginate a SQLAlchemy query.
    
    Usage:
        users = User.query.filter_by(active=True)
        result = paginate_query(users, page=1, per_page=20)
        return jsonify(result)
    
    Returns:
        dict: {
            'items': [...],
            'total': 100,
            'page': 1,
            'per_page': 20,
            'total_pages': 5
        }
    """
    # Enforce limits
    per_page = min(per_page, max_per_page)
    
    # Get paginated results
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }


# ===== XP AWARD HELPERS =====

def award_xp_for_action(user, action_type, **kwargs):
    """
    Simplified wrapper for awarding standard XP amounts.
    
    Usage:
        result = award_xp_for_action(user, 'challenge', 
                                     description='Completed Python challenge')
    """
    from app.services.xp_service import XPService
    
    return XPService.award_standard_xp(
        user=user,
        action_type=action_type,
        description=kwargs.get('description', ''),
        related_entity_type=kwargs.get('related_entity_type'),
        related_entity_id=kwargs.get('related_entity_id')
    )


def award_custom_xp(user, amount, source, description="", **kwargs):
    """
    Simplified wrapper for awarding custom XP amounts.
    
    Usage:
        result = award_custom_xp(user, 150, 'project', 
                                 'Submitted complex project')
    """
    from app.services.xp_service import XPService
    
    return XPService.award_xp(
        user=user,
        amount=amount,
        source=source,
        description=description,
        related_entity_type=kwargs.get('related_entity_type'),
        related_entity_id=kwargs.get('related_entity_id'),
        bypass_cap=kwargs.get('bypass_cap', False)
    )


# ===== VALIDATION HELPERS =====

def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in request data.
    
    Usage:
        error = validate_required_fields(request.json, ['email', 'password'])
        if error:
            return error_response(error)
    
    Returns:
        str or None: Error message if validation fails, None if valid
    """
    if not data:
        return "Request body cannot be empty"

    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
        elif data[field] is None:
            missing.append(field)
        elif isinstance(data[field], str) and str(data[field]).strip() == "":
            missing.append(field)

    if missing:
        return f"Missing or empty required fields: {', '.join(missing)}"

    return None


def validate_positive_integer(value, field_name="value"):
    """
    Validate that a value is a positive integer.

    Rejects bool values (True/False) even though bool is a subclass of int
    in Python.

    Returns:
        str or None: Error message if invalid, None if valid
    """
    if isinstance(value, bool):
        return f"{field_name} must be an integer"

    if not isinstance(value, int):
        return f"{field_name} must be an integer"

    if value <= 0:
        return f"{field_name} must be positive"

    return None


# ===== GET CURRENT USER HELPER =====

def get_current_user():
    """
    Get current authenticated user from JWT.

    Returns None for personnel tokens (prefix "personnel_") and for any
    identity that cannot be resolved to an integer user ID.

    Usage:
        @jwt_required()
        def my_route():
            user = get_current_user()
            if not user:
                return error_response('User not found', 404)

    Returns:
        User or None
    """
    identity = get_jwt_identity()
    if isinstance(identity, str) and identity.startswith("personnel_"):
        return None
    if identity is None:
        return None
    user_id = int(identity)
    return db.session.get(User, user_id)


# ===== SKILL HELPERS =====

def get_available_skills():
    """
    Get list of all available skills.
    
    Returns:
        list: Available skill names
    """
    from app.constants.gamification import AVAILABLE_SKILLS
    return AVAILABLE_SKILLS


def validate_skill_name(skill_name):
    """
    Check if skill name is valid.
    
    Returns:
        bool: True if valid, False otherwise
    """
    from app.constants.gamification import AVAILABLE_SKILLS
    return skill_name in AVAILABLE_SKILLS


# ===== LEADERBOARD HELPERS =====

def get_user_rank(user, metric='xp'):
    """
    Get user's rank for a specific metric.
    
    Args:
        user: User instance
        metric: 'xp', 'streak', or skill name
        
    Returns:
        int: User's rank (1 = first place)
    """
    if metric == 'xp':
        rank = User.query.filter(User.xp > user.xp).count() + 1
    elif metric == 'streak':
        rank = User.query.filter(User.current_streak > user.current_streak).count() + 1
    else:
        # Assume it's a skill name
        from app.models.user_skill import UserSkill
        user_skill = UserSkill.query.filter_by(
            user_id=user.id,
            skill_name=metric
        ).first()
        
        if not user_skill:
            return None
        
        rank = UserSkill.query.filter(
            UserSkill.skill_name == metric,
            UserSkill.xp > user_skill.xp
        ).count() + 1
    
    return rank

