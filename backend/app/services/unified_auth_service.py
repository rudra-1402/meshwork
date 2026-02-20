"""
Unified Authentication Service

Handles authentication for both students and personnel through a single interface.
"""

from app.models.user import User
from app.models.college_personnel import CollegePersonnel
from app.services.auth_services import create_user
from app.services.college_personnel_services import authenticate_personnel, create_personnel
from app.services.email_validation_service import EmailValidationService
from app.extensions import db


class UnifiedAuthService:
    """Service for unified authentication operations"""
    
    @staticmethod
    def validate_email_realtime(email):
        """
        Validates email and returns user type, college info, and registration status.
        
        Args:
            email (str): Email to validate
            
        Returns:
            dict: Validation result with user type and college info
        """
        if not email:
            return {
                'valid': False,
                'error': 'Email is required'
            }
        
        # Check if already registered
        existing_user = User.query.filter_by(email=email).first()
        existing_personnel = CollegePersonnel.query.filter_by(email=email).first()
        
        if existing_user:
            return {
                'valid': False,
                'is_registered': True,
                'error': 'Email already registered',
                'user_type': 'student',
                'college_id': existing_user.college_id,
                'college_name': existing_user.college.name if existing_user.college else None,
                'show_role_selector': False,
            }

        if existing_personnel:
            return {
                'valid': False,
                'is_registered': True,
                'error': 'Email already registered',
                'user_type': 'personnel',
                'college_id': existing_personnel.college_id,
                'college_name': existing_personnel.college.name if existing_personnel.college else None,
                'detected_role': existing_personnel.role,
                'show_role_selector': True,
            }
        
        # Detect user type from email
        user_type_result = UnifiedAuthService.detect_user_type(email)
        
        if not user_type_result['success']:
            return {
                'valid': False,
                'error': user_type_result['error']
            }
        
        # Build response
        return {
            'valid': True,
            'user_type': user_type_result['user_type'],
            'college_id': user_type_result['college_id'],
            'college_name': user_type_result['college_name'],
            'detected_role': user_type_result.get('detected_role'),
            'is_registered': False,
            'whitelisted': user_type_result.get('whitelisted', False),
            'show_role_selector': user_type_result['user_type'] == 'personnel'
        }
    
    @staticmethod
    def detect_user_type(email):
        """
        Detects whether email belongs to a student or personnel.
        
        Args:
            email (str): Email to analyze
            
        Returns:
            dict: {
                'success': bool,
                'user_type': 'student' | 'personnel' | None,
                'college_id': int,
                'college_name': str,
                'detected_role': str (optional, for personnel),
                'whitelisted': bool (for students),
                'error': str (if not successful)
            }
        """
        # Extract domain
        domain = EmailValidationService.extract_domain(email)
        if not domain:
            return {
                'success': False,
                'error': 'Invalid email format'
            }
        
        # Find college by domain
        college = EmailValidationService.find_college_by_domain(domain)
        if not college:
            return {
                'success': False,
                'error': 'College not found for this email domain'
            }
        
        # Try to match student pattern first
        if college.student_email_pattern:
            student_match = EmailValidationService.matches_pattern(
                email, college.student_email_pattern
            )
            
            if student_match:
                # Validate against whitelist
                student_validation = EmailValidationService.validate_student_email(email)
                
                if student_validation['valid']:
                    return {
                        'success': True,
                        'user_type': 'student',
                        'college_id': college.id,
                        'college_name': college.name,
                        'whitelisted': True
                    }
                else:
                    return {
                        'success': False,
                        'error': student_validation['error']
                    }
        
        # Try to match personnel pattern
        if college.personnel_email_pattern:
            personnel_match = EmailValidationService.matches_pattern(
                email, college.personnel_email_pattern
            )
            
            if personnel_match:
                return {
                    'success': True,
                    'user_type': 'personnel',
                    'college_id': college.id,
                    'college_name': college.name,
                    'detected_role': None  # Could be enhanced to detect role from email
                }
        
        # No pattern matched
        return {
            'success': False,
            'error': 'Email does not match student or personnel pattern for this college'
        }
    
    @staticmethod
    def unified_login(email, password):
        """
        Handles login for both students and personnel.
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            dict: {
                'success': bool,
                'user': dict (user info),
                'dashboard_route': str,
                'message': str,
                'token': str (JWT token)
            }
        """
        # Try student login first
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Student login successful
            from flask_jwt_extended import create_access_token
            from app.services.streak_service import StreakService
            from app.services.xp_service import XPService
            
            # Update streak
            streak_result = StreakService.update_login_streak(user)
            
            # Award XP if first login today (use structured fields, not human-readable message)
            xp_awarded = 0
            if streak_result.get('streak_continued') or streak_result.get('first_login_today'):
                xp_result = XPService.award_standard_xp(user, 'daily_login')
                xp_awarded = xp_result.get('xp_awarded', 0)
            
            # Create token
            token = create_access_token(identity=str(user.id))
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'username': user.username,
                    'email': user.email,
                    'role': 'student',
                    'college_name': user.college.name if user.college else None,
                    'xp': user.xp,
                    'level': user.level,
                    'streak': streak_result['current_streak']
                },
                'dashboard_route': '/dashboard',
                'message': f"Welcome back! 🔥 {streak_result['current_streak']} day streak!" if xp_awarded else "Welcome back!",
                'token': token,
                'xp_awarded': xp_awarded
            }
        
        # Try personnel login
        personnel = CollegePersonnel.query.filter_by(email=email).first()
        if personnel and personnel.check_password(password):
            # Personnel login successful
            from flask_jwt_extended import create_access_token
            
            # Create token
            token = create_access_token(identity=f"personnel_{personnel.id}")
            
            return {
                'success': True,
                'user': {
                    'id': personnel.id,
                    'name': f"{personnel.first_name} {personnel.last_name}",
                    'email': personnel.email,
                    'role': personnel.role,
                    'college_name': personnel.college.name if personnel.college else None,
                    'personnel_id': personnel.personnel_id
                },
                'dashboard_route': '/personnel/dashboard',
                'message': f"Welcome {personnel.first_name}!",
                'token': token
            }
        
        # Login failed
        return {
            'success': False,
            'message': 'Invalid email or password'
        }
    
    @staticmethod
    def unified_signup(data):
        """
        Handles signup for both students and personnel.
        
        Args:
            data (dict): Signup data including user_type
            
        Returns:
            dict: {
                'success': bool,
                'user': dict (user info),
                'dashboard_route': str,
                'message': str,
                'token': str (JWT token)
            }
        """
        user_type = data.get('user_type')
        
        if user_type == 'student':
            return UnifiedAuthService._signup_student(data)
        elif user_type == 'personnel':
            return UnifiedAuthService._signup_personnel(data)
        else:
            return {
                'success': False,
                'message': 'Invalid user type'
            }
    
    @staticmethod
    def _signup_student(data):
        """Handle student signup"""
        from flask_jwt_extended import create_access_token
        from app.services.whitelist_service import WhitelistService
        from app.services.xp_service import XPService
        
        # Validate email again
        email_validation = EmailValidationService.validate_student_email(data['email'])
        if not email_validation['valid']:
            return {
                'success': False,
                'message': email_validation['error']
            }
        
        # Check username availability
        username_check = EmailValidationService.check_username_availability(data['username'])
        if not username_check['available']:
            return {
                'success': False,
                'message': username_check['message']
            }
        
        # Use validated college_id from email validation, fall back to submitted value
        validated_college_id = email_validation.get('college_id') or int(data['college_id'])

        # Create user
        user = create_user(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            college_id=validated_college_id
        )

        if not user:
            return {
                'success': False,
                'message': 'Failed to create account'
            }

        # Mark email as registered
        if email_validation.get('whitelist_entry_id'):
            WhitelistService.mark_email_registered(data['email'], validated_college_id, user.id)
        
        # Award signup XP using the canonical constant from XP_AMOUNTS
        signup_xp = XPService.award_standard_xp(
            user=user,
            action_type='account_created',
            description='Welcome bonus for creating account'
        )
        
        # Create token and auto-login
        token = create_access_token(identity=str(user.id))
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'username': user.username,
                'email': user.email,
                'role': 'student',
                'college_name': user.college.name if user.college else None
            },
            'dashboard_route': '/dashboard',
            'message': f"Welcome {user.first_name}! +{signup_xp.get('xp_awarded', 50)} bonus XP! 🎉",
            'token': token
        }
    
    @staticmethod
    def _signup_personnel(data):
        """Handle personnel signup"""
        from flask_jwt_extended import create_access_token
        
        # Validate email against personnel pattern
        email_validation = EmailValidationService.validate_personnel_email(
            data['email'],
            int(data['college_id'])
        )
        
        if not email_validation['valid']:
            return {
                'success': False,
                'message': email_validation['error']
            }
        
        # Create personnel
        success, message, personnel = create_personnel(
            college_id=int(data['college_id']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            role=data['role'],
            personnel_id=data.get('personnel_id')
        )
        
        if not success:
            return {
                'success': False,
                'message': message
            }
        
        # Create token and auto-login
        token = create_access_token(identity=f"personnel_{personnel.id}")
        
        return {
            'success': True,
            'user': {
                'id': personnel.id,
                'name': f"{personnel.first_name} {personnel.last_name}",
                'email': personnel.email,
                'role': personnel.role,
                'college_name': personnel.college.name if personnel.college else None
            },
            'dashboard_route': '/personnel/dashboard',
            'message': f"Welcome {personnel.first_name}!",
            'token': token
        }
