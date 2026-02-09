"""
Profile Routes

User profile endpoints with gamification stats.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.services.xp_service import XPService
from app.services.skill_service import SkillService
from app.services.streak_service import StreakService
from app.models.xp_transaction import XPTransaction

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user's complete profile with gamification stats.
    
    Returns:
        200: Profile data with XP, skills, streak info
        404: User not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Basic profile with gamification stats
    profile = user.get_profile_summary()
    
    # Today's XP breakdown
    xp_summary = XPService.get_daily_summary(user)
    
    # Skill profile
    skill_profile = SkillService.get_user_skill_profile(user.id, limit=10)
    
    # Streak status
    streak_status = StreakService.get_streak_status(user)
    
    # Streak milestones
    all_milestones = StreakService.get_all_milestones()
    
    return jsonify({
        'success': True,
        'profile': profile,
        'xp_summary': xp_summary,
        'skills': skill_profile,
        'streak': streak_status,
        'streak_milestones': all_milestones
    }), 200


@profile_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_profile(user_id):
    """
    Get another user's public profile.
    
    Args:
        user_id: Target user ID
        
    Returns:
        200: Public profile data
        404: User not found
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Public profile (no daily XP details)
    profile = user.get_profile_summary()
    
    # Public skill profile
    skill_profile = SkillService.get_user_skill_profile(user.id, limit=5)
    
    # Public streak status (no "at risk" info)
    streak_status = {
        'current_streak': user.current_streak,
        'max_streak': user.max_streak
    }
    
    return jsonify({
        'success': True,
        'profile': profile,
        'skills': skill_profile,
        'streak': streak_status
    }), 200


@profile_bp.route('/xp-history', methods=['GET'])
@jwt_required()
def get_xp_history():
    """
    Get current user's XP transaction history.
    
    Query Params:
        limit: Number of transactions (default: 50, max: 100)
        source: Filter by source (optional)
        
    Returns:
        200: Transaction history
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Parse query params
    limit = min(int(request.args.get('limit', 50)), 100)
    source_filter = request.args.get('source')
    
    # Get transactions
    transactions = XPTransaction.get_user_history(
        user_id=user.id,
        limit=limit,
        source_filter=source_filter
    )
    
    return jsonify({
        'success': True,
        'total_xp': user.xp,
        'daily_xp_earned': user.daily_xp_earned,
        'transaction_count': len(transactions),
        'transactions': [
            {
                'id': t.id,
                'amount': t.amount,
                'source': t.source,
                'description': t.description,
                'balance_before': t.balance_before,
                'balance_after': t.balance_after,
                'created_at': t.created_at.isoformat(),
                'related_entity_type': t.related_entity_type,
                'related_entity_id': t.related_entity_id
            }
            for t in transactions
        ]
    }), 200


@profile_bp.route('/level-progress', methods=['GET'])
@jwt_required()
def get_level_progress():
    """
    Get detailed level progress information.
    
    Returns:
        200: Level progress data
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    progress = user.get_xp_for_next_level()
    
    return jsonify({
        'success': True,
        'level_progress': progress
    }), 200


@profile_bp.route('/streak-status', methods=['GET'])
@jwt_required()
def get_streak_status():
    """
    Get detailed streak status with risk warning.
    
    Returns:
        200: Streak status and risk info
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get streak status
    status = StreakService.get_streak_status(user)
    
    # Check if at risk
    at_risk = StreakService.check_streak_at_risk(user)
    
    return jsonify({
        'success': True,
        'streak': status,
        'at_risk': at_risk
    }), 200


@profile_bp.route('/skills', methods=['GET'])
@jwt_required()
def get_skills():
    """
    Get current user's skill breakdown.
    
    Query Params:
        limit: Number of top skills (default: 10)
        
    Returns:
        200: Skill profile
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    limit = min(int(request.args.get('limit', 10)), 50)
    
    skill_profile = SkillService.get_user_skill_profile(user.id, limit=limit)
    
    return jsonify({
        'success': True,
        'skills': skill_profile
    }), 200


@profile_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Get comprehensive user statistics.
    
    Returns:
        200: All stats in one response
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get all stats
    profile = user.get_profile_summary()
    xp_summary = XPService.get_daily_summary(user)
    skill_profile = SkillService.get_user_skill_profile(user.id, limit=5)
    streak_status = StreakService.get_streak_status(user)
    at_risk = StreakService.check_streak_at_risk(user)
    
    return jsonify({
        'success': True,
        'profile': profile,
        'daily_xp': xp_summary,
        'top_skills': skill_profile['top_skills'],
        'streak': streak_status,
        'streak_at_risk': at_risk.get('at_risk', False)
    }), 200