from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.auth_services import authenticate_user, create_user
from app.utils.validators import is_empty, is_valid_email
from flask_jwt_extended import create_access_token, unset_jwt_cookies, set_access_cookies
from app.models.college import College
from app.services.xp_service import XPService
from app.services.streak_service import StreakService


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
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        college_id = request.form.get("college_id")

        if is_empty(username) or is_empty(email) or is_empty(password) or is_empty(confirm_password) or is_empty(college_id):
            flash("All fields are required.", "error")
            return redirect(url_for("auth.user_signup"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth.user_signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.user_signup"))

        user = create_user(
            username=username,
            email=email,
            password=password,
            college_id=int(college_id)
        )

        if not user:
            flash("Account with this email already exists.", "error")
            return redirect(url_for("auth.user_signup"))
        
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

        flash(f"Account created successfully! +{signup_xp.get('xp_awarded', 50)} bonus XP! 🎉", "success")
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