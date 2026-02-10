from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.auth_services import authenticate_user, create_user, check_username_availability
from app.utils.validators import is_empty, is_valid_email
from flask_jwt_extended import create_access_token, unset_jwt_cookies, set_access_cookies
from app.models.college import College
from app.services.xp_service import XPService
from app.services.streak_service import StreakService
from app.services.email_validation_service import EmailValidationService
from app.services.whitelist_service import WhitelistService


auth_routes = Blueprint("auth", __name__)

# ================= USER LOGIN =================
@auth_routes.route("/login/user", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if is_empty(email) or is_empty(password):
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.user_login"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth.user_login"))

        result = authenticate_user(email, password)

        if result["success"]:
            user = result["user"]
            
            # ===== GAMIFICATION: Update streak and award login XP =====
            streak_result = StreakService.update_login_streak(user)
            
            # Only award daily login XP if this is first login today
            # (streak_result message will be "Already logged in today" if not first login)
            if streak_result.get('message') != 'Already logged in today':
                xp_result = XPService.award_standard_xp(user, 'daily_login')
                xp_awarded = xp_result.get('xp_awarded', 0)
            else:
                xp_awarded = 0
            
            # Create JWT access token with STRING identity (Flask-JWT-Extended requirement)
            access_token = create_access_token(identity=str(user.id))
            
            # Store token in HTTP-only cookie using Flask-JWT-Extended
            response = redirect(url_for("dashboard.dashboard"))
            set_access_cookies(response, access_token)
            
            # Enhanced flash message with streak info
            if streak_result.get('message') == 'Already logged in today':
                flash(f"Welcome back! You've already logged in today. Current streak: {streak_result['current_streak']} days 🔥", "info")
            elif streak_result['current_streak'] > 1:
                flash(f"Welcome back! 🔥 {streak_result['current_streak']} day streak! +{xp_awarded} XP", "success")
            else:
                flash(f"Logged in successfully! Your streak has started! 🚀 +{xp_awarded} XP", "success")
            return response

        flash(result["message"], "error")
        return redirect(url_for("auth.user_login"))

    return render_template("auth/login_user.html")


# ================= USER SIGNUP =================
@auth_routes.route("/signup/user", methods=["GET", "POST"])
def user_signup():
    colleges = College.query.all()

    if request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        college_id = request.form.get("college_id")  # May be auto-filled

        # Validate required fields
        if is_empty(username) or is_empty(first_name) or is_empty(last_name) or is_empty(email) or is_empty(password) or is_empty(confirm_password):
            flash("All fields are required.", "error")
            return redirect(url_for("auth.user_signup"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth.user_signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.user_signup"))

        # Validate email against whitelist and pattern
        email_validation = EmailValidationService.validate_student_email(email)
        
        if not email_validation['valid']:
            flash(email_validation['error'], "error")
            return redirect(url_for("auth.user_signup"))
        
        # Use college_id from validation if not provided
        if not college_id or college_id == '':
            college_id = email_validation['college_id']

        # Check username availability
        username_check = EmailValidationService.check_username_availability(username)
        if not username_check['available']:
            flash(username_check['message'], "error")
            return redirect(url_for("auth.user_signup"))

        # Create user with new fields
        user = create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            college_id=int(college_id)
        )

        if not user:
            flash("Account with this email or username already exists.", "error")
            return redirect(url_for("auth.user_signup"))
        
        # Mark email as registered in whitelist
        if email_validation.get('whitelist_entry_id'):
            WhitelistService.mark_email_registered(email, user.id)
        
        # ===== GAMIFICATION: Award signup bonus XP =====
        # Note: Streak starts at 0, first login will set streak to 1
        signup_xp = XPService.award_xp(
            user=user,
            amount=50,
            source='account_created',
            description='Welcome bonus for creating account'
        )
        
        # ✅ AUTO LOGIN with JWT with STRING identity (Flask-JWT-Extended requirement)
        access_token = create_access_token(identity=str(user.id))
        
        response = redirect(url_for("scoring.questionnaire_form"))
        set_access_cookies(response, access_token)

        flash(f"Welcome {user.first_name}! Account created successfully! +{signup_xp.get('xp_awarded', 50)} bonus XP! 🎉", "success")
        return response

    return render_template(
        "auth/signup_user.html",
        colleges=colleges
    )


# ================= USER LOGOUT =================
@auth_routes.route("/logout")
def logout():
    response = redirect(url_for("main_routes.landing"))
    unset_jwt_cookies(response)  # Clear JWT cookies
    flash("Logged out successfully.", "success")
    return response


# ================= API ENDPOINTS =================
@auth_routes.route("/api/check-username", methods=["POST"])
def check_username_api():
    """
    API endpoint to check username availability (for AJAX).
    """
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'available': False, 'error': 'Username required'}), 400
    
    result = EmailValidationService.check_username_availability(username)
    return jsonify(result), 200


@auth_routes.route("/api/detect-college", methods=["POST"])
def detect_college_api():
    """
    API endpoint to detect college from email (for AJAX).
    """
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Validate and detect college
    validation = EmailValidationService.validate_student_email(email)
    
    if validation['valid']:
        return jsonify({
            'success': True,
            'college_id': validation['college_id'],
            'college_name': validation['college_name'],
            'whitelisted': validation['whitelisted']
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': validation['error']
        }), 400