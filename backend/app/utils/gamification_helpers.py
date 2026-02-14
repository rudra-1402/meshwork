"""
Gamification Helper Utilities

Common utilities for gamification features.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.college import College


# ===== DECORATOR: Admin Required =====

def admin_required(fn):
    """
    Decorator to require admin/college privileges.
    
    Usage:
        @app.route('/admin/endpoint')
        @admin_required
        def admin_endpoint():
            # Only admins can access this
            pass
    
    Modify the logic inside to match your admin check system.
    """
    from flask_jwt_extended import jwt_required
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # ===== CUSTOMIZE THIS LOGIC =====
        # Option 1: Check if user has college association
        if not user.college_id:
            return jsonify({
                'success': False,
                'error': 'Admin privileges required'
            }), 403
        
        # Option 2: Check if user has is_admin flag (if you add this field)
        # if not user.is_admin:
        #     return jsonify({'error': 'Admin only'}), 403
        
        # Option 3: Check user role in college
        # college = College.query.get(user.college_id)
        # if not college or user.id != college.admin_id:
        #     return jsonify({'error': 'Not authorized'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


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
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get community_id from kwargs or args
        community_id = kwargs.get('community_id') or args[0] if args else None
        
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
    
    missing = [field for field in required_fields if field not in data]
    
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    
    return None


def validate_positive_integer(value, field_name="value"):
    """
    Validate that a value is a positive integer.
    
    Returns:
        str or None: Error message if invalid, None if valid
    """
    if not isinstance(value, int):
        return f"{field_name} must be an integer"
    
    if value <= 0:
        return f"{field_name} must be positive"
    
    return None


# ===== GET CURRENT USER HELPER =====

def get_current_user():
    """
    Get current authenticated user from JWT.
    
    Usage:
        @jwt_required()
        def my_route():
            user = get_current_user()
            if not user:
                return error_response('User not found', 404)
    
    Returns:
        User or None
    """
    user_id = get_jwt_identity()
    return User.query.get(user_id)


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


# ===== USAGE EXAMPLES =====

"""
EXAMPLE 1: Using decorators

from app.utils.gamification_helpers import admin_required, success_response

@app.route('/admin/stats')
@admin_required
def admin_stats():
    # Only admins can access this
    return success_response({'stats': {...}})


EXAMPLE 2: Awarding XP

from app.utils.gamification_helpers import award_xp_for_action

@app.route('/task/complete')
@jwt_required()
def complete_task():
    user = get_current_user()
    result = award_xp_for_action(user, 'task', 
                                  description='Completed community task')
    return success_response({'xp': result})


EXAMPLE 3: Validation

from app.utils.gamification_helpers import validate_required_fields, error_response

@app.route('/create')
def create_item():
    error = validate_required_fields(request.json, ['title', 'description'])
    if error:
        return error_response(error)
    
    # Proceed with creation
    ...
"""