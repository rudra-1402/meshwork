"""
Leaderboard Routes

Leaderboards for XP, streaks, and skills.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.services.xp_service import XPService
from app.services.skill_service import SkillService
from app.services.streak_service import StreakService
from app.constants.gamification import AVAILABLE_SKILLS

leaderboards_bp = Blueprint('leaderboards', __name__)


@leaderboards_bp.route('/xp', methods=['GET'])
@jwt_required()
def xp_leaderboard():
    """
    Get top users by total XP.
    
    Query Params:
        limit: Number of users (default: 10, max: 50)
        
    Returns:
        200: Top users with XP and level
    """
    limit = min(request.args.get('limit', 10, type=int) or 10, 50)

    leaderboard = XPService.get_xp_leaderboard(limit=limit)
    
    return jsonify({
        'success': True,
        'leaderboard_type': 'xp',
        'total_entries': len(leaderboard),
        'leaderboard': leaderboard
    }), 200


@leaderboards_bp.route('/streak', methods=['GET'])
@jwt_required()
def streak_leaderboard():
    """
    Get top users by current streak.
    
    Query Params:
        limit: Number of users (default: 10, max: 50)
        
    Returns:
        200: Top users with streak info
    """
    limit = min(request.args.get('limit', 10, type=int) or 10, 50)

    leaderboard = StreakService.get_streak_leaderboard(limit=limit)
    
    return jsonify({
        'success': True,
        'leaderboard_type': 'streak',
        'total_entries': len(leaderboard),
        'leaderboard': leaderboard
    }), 200


@leaderboards_bp.route('/skill/<skill_name>', methods=['GET'])
def skill_leaderboard(skill_name):
    """
    Get top users for a specific skill.
    
    Args:
        skill_name: Skill name (e.g., "Python", "JavaScript")
        
    Query Params:
        limit: Number of users (default: 10, max: 50)
        
    Returns:
        200: Top users with skill XP and level
        400: Invalid skill name
    """
    # Validate skill name
    if skill_name not in AVAILABLE_SKILLS:
        return jsonify({
            'success': False,
            'error': f'Invalid skill: {skill_name}',
            'available_skills': AVAILABLE_SKILLS
        }), 400
    
    limit = min(request.args.get('limit', 10, type=int) or 10, 50)

    leaderboard = SkillService.get_skill_leaderboard(skill_name, limit=limit)
    
    return jsonify({
        'success': True,
        'leaderboard_type': 'skill',
        'skill_name': skill_name,
        'total_entries': len(leaderboard),
        'leaderboard': leaderboard
    }), 200


@leaderboards_bp.route('/skills/available', methods=['GET'])
def available_skills():
    """
    Get list of all available skills for leaderboards.
    
    Returns:
        200: List of skill names
    """
    return jsonify({
        'success': True,
        'total_skills': len(AVAILABLE_SKILLS),
        'skills': AVAILABLE_SKILLS
    }), 200


@leaderboards_bp.route('/all', methods=['GET'])
@jwt_required()
def all_leaderboards():
    """
    Get all leaderboards in one response.
    
    Returns:
        200: All leaderboards (XP, streak, top 3 skills)
    """
    limit = 10
    
    # XP leaderboard
    xp_board = XPService.get_xp_leaderboard(limit=limit)
    
    # Streak leaderboard
    streak_board = StreakService.get_streak_leaderboard(limit=limit)
    
    # Top 3 most popular skills (Python, JavaScript, React as examples)
    # You can make this dynamic based on user activity
    top_skills = ['Python', 'JavaScript', 'React']
    skill_boards = {}
    
    for skill in top_skills:
        if skill in AVAILABLE_SKILLS:
            skill_boards[skill] = SkillService.get_skill_leaderboard(skill, limit=5)
    
    return jsonify({
        'success': True,
        'xp_leaderboard': xp_board,
        'streak_leaderboard': streak_board,
        'skill_leaderboards': skill_boards
    }), 200


@leaderboards_bp.route('/my-rank', methods=['GET'])
@jwt_required()
def my_rank():
    """
    Get current user's rank in all leaderboards.
    
    Returns:
        200: User's rank in XP, streak, and their top skills
    """
    from flask_jwt_extended import get_jwt_identity
    from app.models.user import User
    from sqlalchemy import func
    
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # XP rank
    xp_rank = (
        User.query
        .filter(User.xp > user.xp)
        .count()
    ) + 1
    
    # Streak rank
    streak_rank = (
        User.query
        .filter(User.current_streak > user.current_streak)
        .count()
    ) + 1
    
    # Top skill ranks
    from app.models.user_skill import UserSkill
    
    user_skills = UserSkill.query.filter_by(user_id=user.id).order_by(UserSkill.xp.desc()).limit(3).all()
    
    skill_ranks = []
    for skill in user_skills:
        rank = (
            UserSkill.query
            .filter(
                UserSkill.skill_name == skill.skill_name,
                UserSkill.xp > skill.xp
            )
            .count()
        ) + 1
        
        skill_ranks.append({
            'skill_name': skill.skill_name,
            'rank': rank,
            'xp': skill.xp,
            'level': skill.level
        })
    
    return jsonify({
        'success': True,
        'user_id': user.id,
        'username': user.username,
        'xp_rank': xp_rank,
        'total_xp': user.xp,
        'streak_rank': streak_rank,
        'current_streak': user.current_streak,
        'skill_ranks': skill_ranks
    }), 200