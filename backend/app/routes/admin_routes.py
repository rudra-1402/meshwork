"""
Admin Routes

Admin-only routes for XP management, penalties, and bonuses.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.models.college import College
from app.services.xp_service import XPService
from app.services.skill_service import SkillService

admin_bp = Blueprint('admin', __name__)


# ===== ADMIN DECORATOR =====
# You'll need to create this decorator based on your admin check logic

def admin_required(fn):
    """
    Decorator to require admin/college privileges.
    
    Modify this to match your existing admin check logic.
    """
    from functools import wraps
    
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        
        # TODO: Replace with your actual admin check
        # Example: Check if user is a college admin
        if not user or not user.college_id:
            return jsonify({
                'success': False,
                'error': 'Admin privileges required'
            }), 403
        
        college = db.session.get(College, user.college_id)
        if not college:
            return jsonify({
                'success': False,
                'error': 'Invalid college association'
            }), 403
        
        if not user.is_admin:
            return jsonify({'success': False, 'error': 'Admin only'}), 403

        return fn(*args, **kwargs)
    
    return wrapper


# ===== XP PENALTY ROUTES =====

@admin_bp.route('/penalty/<int:user_id>', methods=['POST'])
@admin_required
def apply_penalty(user_id):
    """
    Remove XP from user for violations (plagiarism, spam, etc.).
    
    Request Body:
        amount: XP to remove (required)
        reason: Reason for penalty (required)
        related_entity_type: Optional entity type
        related_entity_id: Optional entity ID
        
    Returns:
        200: Penalty applied successfully
        400: Invalid request
        404: User not found
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    data = request.get_json(silent=True)

    # Validate input
    if not data or 'amount' not in data or 'reason' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: amount, reason'
        }), 400

    amount = data.get('amount')
    reason = data.get('reason')

    if not isinstance(amount, int) or amount <= 0:
        return jsonify({
            'success': False,
            'error': 'Amount must be a positive integer'
        }), 400

    if not reason or len(reason.strip()) == 0:
        return jsonify({
            'success': False,
            'error': 'Reason cannot be empty'
        }), 400

    # Apply penalty
    result = XPService.remove_xp(
        user=user,
        amount=amount,
        reason=reason,
        related_entity_type=data.get('related_entity_type'),
        related_entity_id=data.get('related_entity_id')
    )
    
    return jsonify({
        'success': True,
        'penalty': result,
        'user': {
            'id': user.id,
            'username': user.username,
            'xp': user.xp,
            'level': user.level
        }
    }), 200


@admin_bp.route('/bonus/<int:user_id>', methods=['POST'])
@admin_required
def award_bonus(user_id):
    """
    Award bonus XP to user (bypasses daily cap).
    
    Request Body:
        amount: XP to award (required)
        reason: Reason for bonus (required)
        
    Returns:
        200: Bonus awarded successfully
        400: Invalid request
        404: User not found
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    data = request.get_json(silent=True)

    # Validate input
    if not data or 'amount' not in data or 'reason' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: amount, reason'
        }), 400

    amount = data.get('amount')
    reason = data.get('reason')

    if not isinstance(amount, int) or amount <= 0:
        return jsonify({
            'success': False,
            'error': 'Amount must be a positive integer'
        }), 400

    # Award bonus (bypasses daily cap)
    result = XPService.award_xp(
        user=user,
        amount=amount,
        source='admin_bonus',
        description=reason,
        bypass_cap=True  # Admin bonuses bypass daily cap
    )
    
    return jsonify({
        'success': True,
        'bonus': result,
        'user': {
            'id': user.id,
            'username': user.username,
            'xp': user.xp,
            'level': user.level
        }
    }), 200


@admin_bp.route('/skill-xp/<int:user_id>', methods=['POST'])
@admin_required
def award_skill_xp(user_id):
    """
    Manually award skill XP to user.
    
    Request Body:
        skill_name: Skill name (required)
        amount: XP to award (required)
        reason: Reason for award (optional)
        
    Returns:
        200: Skill XP awarded successfully
        400: Invalid request
        404: User not found
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    data = request.get_json(silent=True)

    # Validate input
    if not data or 'skill_name' not in data or 'amount' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: skill_name, amount'
        }), 400
    
    skill_name = data.get('skill_name')
    amount = data.get('amount')
    reason = data.get('reason', 'Admin manual award')

    from app.constants.gamification import AVAILABLE_SKILLS
    if skill_name not in AVAILABLE_SKILLS:
        return jsonify({
            'success': False,
            'error': f'Invalid skill. Must be one of: {list(AVAILABLE_SKILLS)}'
        }), 400

    # Award skill XP
    result = SkillService.award_skill_xp(
        user_id=user.id,
        skill_name=skill_name,
        amount=amount,
        source='admin_manual'
    )
    
    if not result.get('success'):
        return jsonify(result), 400
    
    return jsonify({
        'success': True,
        'skill_award': result,
        'user': {
            'id': user.id,
            'username': user.username
        }
    }), 200


@admin_bp.route('/user-stats/<int:user_id>', methods=['GET'])
@admin_required
def get_user_stats(user_id):
    """
    Get detailed user stats for admin review.
    
    Returns:
        200: Complete user stats
        404: User not found
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    # Get all stats
    profile = user.get_profile_summary()
    xp_summary = XPService.get_daily_summary(user)
    skill_profile = SkillService.get_user_skill_profile(user.id, limit=20)
    
    # Get recent transactions
    from app.models.xp_transaction import XPTransaction
    recent_transactions = XPTransaction.get_user_history(user.id, limit=20)
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'gamification': {
            'profile': profile,
            'daily_xp': xp_summary,
            'skills': skill_profile,
            'recent_transactions': [
                {
                    'amount': t.amount,
                    'source': t.source,
                    'description': t.description,
                    'created_at': t.created_at.isoformat()
                }
                for t in recent_transactions
            ]
        }
    }), 200


@admin_bp.route('/bulk-bonus', methods=['POST'])
@admin_required
def bulk_bonus():
    """
    Award bonus XP to multiple users at once.
    
    Request Body:
        user_ids: List of user IDs (required)
        amount: XP to award each user (required)
        reason: Reason for bonus (required)
        
    Returns:
        200: Bulk bonus results
        400: Invalid request
    """
    data = request.get_json(silent=True)

    # Validate input
    if not data or 'user_ids' not in data or 'amount' not in data or 'reason' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: user_ids, amount, reason'
        }), 400
    
    user_ids = data.get('user_ids')
    amount = data.get('amount')
    reason = data.get('reason')
    
    MAX_BULK_TARGETS = 100
    if not isinstance(user_ids, list) or len(user_ids) == 0:
        return jsonify({
            'success': False,
            'error': 'user_ids must be a non-empty list'
        }), 400

    if len(user_ids) > MAX_BULK_TARGETS:
        return jsonify({
            'success': False,
            'error': f'Cannot process more than {MAX_BULK_TARGETS} users at once'
        }), 400
    
    if not isinstance(amount, int) or amount <= 0:
        return jsonify({
            'success': False,
            'error': 'Amount must be a positive integer'
        }), 400
    
    # Award to each user
    results = []
    
    for user_id in user_ids:
        user = db.session.get(User, user_id)
        
        if not user:
            results.append({
                'user_id': user_id,
                'success': False,
                'error': 'User not found'
            })
            continue
        
        result = XPService.award_xp(
            user=user,
            amount=amount,
            source='admin_bulk_bonus',
            description=reason,
            bypass_cap=True
        )
        
        results.append({
            'user_id': user_id,
            'username': user.username,
            'success': result['success'],
            'xp_awarded': result.get('xp_awarded', 0)
        })
    
    return jsonify({
        'success': True,
        'total_users': len(user_ids),
        'results': results
    }), 200