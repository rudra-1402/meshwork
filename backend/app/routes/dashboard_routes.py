from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.scoring import UserScoring

dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/dashboard")
@jwt_required()
def dashboard():
    """
    User dashboard - requires JWT authentication.
    Shows user info and quick links.
    """
    user_id = int(get_jwt_identity())  # Convert string JWT identity back to int
    
    # Get user info
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for("auth.user_login"))
    
    # Check if user has completed the scoring questionnaire
    scoring = UserScoring.query.filter_by(user_id=user_id).first()
    has_completed_questionnaire = bool(scoring) or user.has_completed_questionnaire
    
    return render_template(
        "dashboard/dashboard.html",
        username=user.username,
        email=user.email,
        has_completed_questionnaire=has_completed_questionnaire,
        role="user"
    )


@dashboard_routes.route("/profile")
@jwt_required()
def profile_page():
    """
    User profile page with questionnaire results.
    """
    user_id = int(get_jwt_identity())  # Convert string JWT identity back to int
    
    # Get user info
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for("auth.user_login"))
    
    # Get scoring info
    scoring = UserScoring.query.filter_by(user_id=user_id).first()
    
    return render_template(
        'dashboard/profile.html',
        user=user,
        scoring=scoring
    )