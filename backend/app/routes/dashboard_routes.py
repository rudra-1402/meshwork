from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.models.college import College
from app.models.scoring import UserScoring
from app.utils.jwt_helpers import get_user_id_or_redirect, get_college_id_or_redirect

dashboard_routes = Blueprint("dashboard", __name__)

@dashboard_routes.route("/dashboard")
@jwt_required()
def dashboard():
    """
    User dashboard - requires JWT authentication.
    Shows user info and quick links.
    """
    user_id, response = get_user_id_or_redirect()
    if response:
        return response
    
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
    user_id, response = get_user_id_or_redirect()
    if response:
        return response
    
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


@dashboard_routes.route("/dashboard/college")
@jwt_required()
def college_dashboard():
    """
    College dashboard - requires JWT authentication.
    Shows college info and student list.
    """
    college_id, response = get_college_id_or_redirect()
    if response:
        return response
    
    # Get college info
    college = College.query.get(college_id)
    if not college:
        flash("College not found", "error")
        return redirect(url_for("college_auth.college_login"))
    
    # Get all users from this college
    users = User.query.filter_by(college_id=college_id).all()
    
    return render_template(
        "dashboard/dashboard.html",
        username=college.name,
        email=college.email,
        role="college",
        college=college,
        users=users,
        user_count=len(users)
    )