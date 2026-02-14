"""
EXAMPLE: Challenge Routes with Gamification

This shows how to integrate XP and skill XP awards into challenge completion.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.extensions import db
from app.services.xp_service import XPService
from app.services.skill_service import SkillService

# This is an EXAMPLE - adjust to match your existing blueprint
challenge_example_bp = Blueprint('challenge_example', __name__, url_prefix='/api/challenges')


# ===== EXAMPLE 1: Challenge Completion with XP + Skill XP =====

@challenge_example_bp.route('/<int:challenge_id>/submit', methods=['POST'])
@jwt_required()
def submit_challenge(challenge_id):
    """
    Submit challenge solution with automatic XP and skill XP award.
    
    Request Body:
        solution: User's solution code (required)
        
    Returns:
        200: Submission successful with XP results
        404: Challenge not found
        400: Invalid submission
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # TODO: Replace with your actual Challenge model
    # This is pseudocode - adjust to your schema
    from app.models.community_task import CommunityTask  # Example - use your model
    
    challenge = CommunityTask.query.get(challenge_id)
    
    if not challenge:
        return jsonify({
            'success': False,
            'error': 'Challenge not found'
        }), 404
    
    data = request.json
    
    if not data or 'solution' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing solution'
        }), 400
    
    # ===== YOUR EXISTING VALIDATION LOGIC HERE =====
    # Check if solution is correct, run tests, etc.
    # For this example, assume it passes
    
    is_correct = True  # Your validation result
    
    if not is_correct:
        return jsonify({
            'success': False,
            'error': 'Solution incorrect'
        }), 400
    
    # ===== GAMIFICATION INTEGRATION START =====
    
    # 1. Award account XP
    xp_amount = 100  # Base XP for challenge
    
    xp_result = XPService.award_xp(
        user=user,
        amount=xp_amount,
        source='challenge',
        description=f'Completed challenge: {challenge.title}',
        related_entity_type='CommunityTask',
        related_entity_id=challenge.id
    )
    
    # 2. Distribute skill XP (if challenge has skill weights)
    skill_result = None
    
    # TODO: Replace with your actual skill weights storage
    # Example: If your challenge model has a 'skill_weights' JSON field
    if hasattr(challenge, 'skill_weights') and challenge.skill_weights:
        skill_result = SkillService.distribute_challenge_xp(
            user_id=user.id,
            total_xp=xp_amount,
            skill_weights=challenge.skill_weights
            # Example: {"Python": 60, "Algorithms": 40}
        )
    
    # ===== GAMIFICATION INTEGRATION END =====
    
    # Save submission to database (your existing logic)
    # ...
    
    return jsonify({
        'success': True,
        'message': 'Challenge completed!',
        'xp': xp_result,
        'skills': skill_result,
        'user': user.get_profile_summary()
    }), 200


# ===== EXAMPLE 2: Challenge Creation (Admin) with Skill Weights =====

@challenge_example_bp.route('/create', methods=['POST'])
@jwt_required()
def create_challenge():
    """
    Create new challenge with skill weights.
    
    Request Body:
        title: Challenge title (required)
        description: Challenge description (required)
        skill_weights: Skill distribution (required)
            Example: {"Python": 60, "SQL": 30, "Docker": 10}
        
    Returns:
        201: Challenge created
        400: Invalid data
    """
    # TODO: Add admin check here
    
    data = request.json
    
    # Validate input
    if not data or 'title' not in data or 'skill_weights' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400
    
    skill_weights = data.get('skill_weights')
    
    # ===== GAMIFICATION INTEGRATION: Validate Skill Weights =====
    
    valid, error_msg = SkillService.validate_skill_weights(skill_weights)
    
    if not valid:
        return jsonify({
            'success': False,
            'error': f'Invalid skill weights: {error_msg}'
        }), 400
    
    # Normalize weights to sum exactly to 100
    normalized_weights = SkillService.normalize_skill_weights(skill_weights)
    
    # ===== CREATE CHALLENGE =====
    
    # TODO: Replace with your actual Challenge model creation
    from app.models.community_task import CommunityTask
    
    challenge = CommunityTask(
        title=data['title'],
        description=data.get('description', ''),
        # Store skill weights as JSON
        # You'll need to add this column to your model:
        # skill_weights = db.Column(db.JSON, nullable=True)
    )
    
    # If your model has skill_weights field:
    # challenge.skill_weights = normalized_weights
    
    db.session.add(challenge)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Challenge created',
        'challenge': {
            'id': challenge.id,
            'title': challenge.title,
            'skill_weights': normalized_weights
        }
    }), 201


# ===== EXAMPLE 3: Get AI Skill Weight Suggestions =====

@challenge_example_bp.route('/suggest-skills', methods=['POST'])
@jwt_required()
def suggest_skills():
    """
    Get AI-suggested skill weights for a challenge.
    
    Request Body:
        title: Challenge title (required)
        description: Challenge description (required)
        
    Returns:
        200: AI-suggested skill weights
    """
    # TODO: Add admin check here
    
    data = request.json
    
    if not data or 'title' not in data or 'description' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400
    
    # Get AI prompt
    prompt_data = SkillService.suggest_skill_weights_for_ai(
        challenge_title=data['title'],
        challenge_description=data['description']
    )
    
    # TODO: Call your Google Gemini API here
    # For now, return the prompt so admin can review
    
    return jsonify({
        'success': True,
        'message': 'AI prompt generated. Call Gemini API with this prompt.',
        'prompt': prompt_data['prompt'],
        'available_skills': prompt_data['available_skills'],
        'min_dominant_weight': prompt_data['min_dominant_weight']
    }), 200


# ===== HOW TO INTEGRATE INTO YOUR EXISTING CHALLENGE ROUTES =====

"""
INTEGRATION STEPS:

1. Find your challenge submission route (probably in app/routes/community_routes.py)

2. Add these imports at the top:
   from app.services.xp_service import XPService
   from app.services.skill_service import SkillService

3. After validating the submission, add:
   
   # Award account XP
   xp_result = XPService.award_xp(
       user=current_user,
       amount=100,
       source='challenge',
       description=f'Completed: {challenge.title}',
       related_entity_type='Challenge',
       related_entity_id=challenge.id
   )
   
   # Award skill XP (if challenge has skill weights)
   if challenge.skill_weights:
       skill_result = SkillService.distribute_challenge_xp(
           user_id=current_user.id,
           total_xp=100,
           skill_weights=challenge.skill_weights
       )

4. Include results in response:
   
   return jsonify({
       'success': True,
       'xp': xp_result,
       'skills': skill_result
   })

5. For challenge creation, validate skill weights:
   
   valid, error = SkillService.validate_skill_weights(skill_weights)
   if not valid:
       return jsonify({'error': error}), 400

IMPORTANT NOTES:

- Replace 'CommunityTask' with your actual Challenge model
- Add 'skill_weights' JSON column to your Challenge model if needed
- Adjust XP amounts based on challenge difficulty
- Consider adding bonus XP for perfect scores
"""
