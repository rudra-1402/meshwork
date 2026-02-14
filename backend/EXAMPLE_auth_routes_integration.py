"""
EXAMPLE: Updated Auth Routes with Gamification

This shows how to integrate streak tracking and XP awards into your existing login flow.
Replace your existing login route with this pattern.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.extensions import db
from app.services.xp_service import XPService
from app.services.streak_service import StreakService

# This is an EXAMPLE - adjust to match your existing blueprint name
auth_example_bp = Blueprint('auth_example', __name__, url_prefix='/api/auth')


# ===== EXAMPLE 1: Login with Streak + XP =====

@auth_example_bp.route('/login', methods=['POST'])
def login():
    """
    User login with automatic streak tracking and XP award.
    
    Request Body:
        email: User email (required)
        password: User password (required)
        
    Returns:
        200: Login successful with streak and XP info
        401: Invalid credentials
        400: Missing fields
    """
    data = request.json
    
    # Validate input
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: email, password'
        }), 400
    
    email = data.get('email')
    password = data.get('password')
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({
            'success': False,
            'error': 'Invalid email or password'
        }), 401
    
    # ===== GAMIFICATION INTEGRATION START =====
    
    # 1. Update login streak
    streak_result = StreakService.update_login_streak(user)
    
    # 2. Award daily login XP (only if not already awarded today)
    xp_result = XPService.award_standard_xp(
        user=user,
        action_type='daily_login'
    )
    
    # Note: If user already logged in today, XP service will handle it gracefully
    
    # ===== GAMIFICATION INTEGRATION END =====
    
    # Create JWT token
    access_token = create_access_token(identity=user.id)
    
    # Return response with gamification data
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.get_profile_summary(),
        'streak': streak_result,
        'xp': xp_result
    }), 200


# ===== EXAMPLE 2: Registration (No Gamification Needed) =====

@auth_example_bp.route('/register', methods=['POST'])
def register():
    """
    User registration.
    
    Gamification fields are automatically initialized with defaults:
    - xp = 0
    - level = 1
    - reputation = 0
    - current_streak = 0
    
    No additional code needed!
    """
    data = request.json
    
    # Validate input
    if not data or 'email' not in data or 'password' not in data or 'username' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'error': 'Email already registered'
        }), 400
    
    # Create user (gamification fields auto-initialize)
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'access_token': access_token,
        'user': user.get_profile_summary()
    }), 201


# ===== EXAMPLE 3: Logout (No Gamification Needed) =====

@auth_example_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout.
    
    No gamification logic needed - streak is based on calendar days,
    not session time.
    """
    # Your logout logic here (clear cookies, etc.)
    
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200


# ===== EXAMPLE 4: Get Current User =====

@auth_example_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user's profile with gamification stats.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'user': user.get_profile_summary()
    }), 200


# ===== HOW TO USE IN YOUR EXISTING CODE =====

"""
INTEGRATION STEPS:

1. Find your existing login route (probably in app/routes/auth_routes.py)

2. Add these imports at the top:
   from app.services.xp_service import XPService
   from app.services.streak_service import StreakService

3. After authenticating the user, add:
   
   # Update streak
   streak_result = StreakService.update_login_streak(user)
   
   # Award login XP
   xp_result = XPService.award_standard_xp(user, 'daily_login')

4. Include streak and xp results in your response:
   
   return jsonify({
       'success': True,
       'user': user.get_profile_summary(),
       'streak': streak_result,
       'xp': xp_result
   })

5. That's it! No changes needed to registration or logout.
"""
