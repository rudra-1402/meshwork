from flask import Blueprint, request, jsonify
from flask import render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.extensions import db
from app.services.scoring_service import ScoringService
from app.exceptions import (
    ValidationError,
    AlreadyScoredError,
    ScoringError,
    NotScoredError
)

logger = logging.getLogger(__name__)

scoring_bp = Blueprint("scoring", __name__)

# Lazy initialization to avoid instantiating service at import time
_scoring_service_instance = None

def get_scoring_service():
    """
    Get or create scoring service instance (lazy initialization).
    This ensures the service is only created when actually needed,
    avoiding Ollama verification during module import.
    """
    global _scoring_service_instance
    if _scoring_service_instance is None:
        logger.info("Initializing ScoringService (lazy load)")
        _scoring_service_instance = ScoringService()
    return _scoring_service_instance

@scoring_bp.route("/questionnaire", methods=["GET"])
@jwt_required()
def questionnaire_form():
    """
    Display the questionnaire form for users who haven't completed it.
    Redirects to profile if already completed.
    """
    user_id = int(get_jwt_identity())  # Convert string JWT identity back to int
    
    from app.models.scoring import UserScoring
    
    # Check if user has already completed questionnaire
    existing_scoring = UserScoring.query.filter_by(user_id=user_id).first()
    if existing_scoring:
        flash("You have already completed the questionnaire.", "info")
        return redirect(url_for('scoring.get_scoring_profile'))
    
    return render_template('auth/questionnaire.html')

@scoring_bp.route("/api/scoring/submit", methods=["POST"])
@jwt_required()
def submit_questionnaire():
    """
    Submit questionnaire - handles both JSON (API) and form data (HTML form).
    """
    user_id = int(get_jwt_identity())  # Convert string JWT identity back to int
    logger.info(f"=== Starting questionnaire submission for user_id={user_id} ===")
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        responses = data.get("responses", {})
    else:
        # Convert form data to expected format
        responses = {
            "q1_project_excitement": request.form.get("q1_project_excitement"),
            "q2_team_roles": request.form.getlist("q2_team_roles"),
            "q2_explanation": request.form.get("q2_explanation"),
            "q3_depth_vs_breadth": int(request.form.get("q3_depth_vs_breadth")),
            "q3_explanation": request.form.get("q3_explanation"),
            "q4_problem_solving": request.form.get("q4_problem_solving"),
            "q5_hackathons": int(request.form.get("q5_hackathons")),
            "q5_competitions": int(request.form.get("q5_competitions")),
            "q5_team_projects": int(request.form.get("q5_team_projects")),
            "q5_open_source": int(request.form.get("q5_open_source")),
            "q5_research": int(request.form.get("q5_research")),
            "q6_technologies": request.form.getlist("q6_technologies"),
            "q6_explanation": request.form.get("q6_explanation", ""),
            "q7_collaboration_style": request.form.get("q7_collaboration_style"),
            "q7_explanation": request.form.get("q7_explanation"),
            "q8_learning_motivation": request.form.get("q8_learning_motivation")
        }
        logger.info(f"Form data parsed for user_id={user_id}")
    
    # Validate responses exist
    if not responses:
        logger.warning(f"No responses provided for user_id={user_id}")
        if request.is_json:
            return jsonify({"error": "Missing 'responses' field"}), 400
        else:
            flash("Please complete all required fields.", "error")
            return redirect(url_for('scoring.questionnaire_form'))
    
    logger.info(f"Received questionnaire submission for user_id={user_id}")
    
    try:
        # Get service instance (lazy initialization)
        scoring_service = get_scoring_service()
        
        # Process questionnaire
        logger.info(f"Starting AI scoring for user_id={user_id}")
        
        # Add timeout protection (30 seconds max for AI scoring)
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("AI scoring exceeded 30 second timeout")
        
        # Set timeout (only on Unix-like systems)
        import platform
        if platform.system() != 'Windows':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
        
        try:
            result = scoring_service.process_initial_questionnaire(user_id, responses)
        finally:
            # Cancel timeout
            if platform.system() != 'Windows':
                signal.alarm(0)
        
        logger.info(f"AI scoring completed for user_id={user_id}: {result}")
        
        # Handle response based on request type
        if request.is_json:
            logger.info(f"Returning JSON response for user_id={user_id}")
            return jsonify({
                "status": "success",
                "message": "Profile completed successfully",
                "data": result
            }), 200
        else:
            logger.info(f"Flashing success message and redirecting user_id={user_id}")
            flash("Profile completed successfully!", "success")
            logger.info(f"Redirecting to dashboard.profile_page for user_id={user_id}")
            response = redirect(url_for('dashboard.profile_page'))
            logger.info(f"=== Successfully completed questionnaire submission for user_id={user_id} ===")
            return response
    
    except AlreadyScoredError as e:
        logger.warning(f"Duplicate questionnaire submission attempt by user_id={user_id}")
        if request.is_json:
            return jsonify({"error": "Questionnaire already submitted", "message": str(e)}), 409
        else:
            flash("You have already completed the questionnaire.", "warning")
            return redirect(url_for('dashboard.dashboard'))
    
    except ValidationError as e:
        logger.warning(f"Questionnaire validation failed for user_id={user_id}: {e}")
        if request.is_json:
            return jsonify({"error": "Invalid questionnaire data", "message": str(e)}), 400
        else:
            flash(f"Validation error: {str(e)}", "error")
            return redirect(url_for('scoring.questionnaire_form'))
    
    except ScoringError as e:
        logger.error(f"AI scoring failed for user_id={user_id}: {e}", exc_info=True)
        if request.is_json:
            return jsonify({"error": "Scoring service temporarily unavailable"}), 503
        else:
            flash("AI Scoring failed. This may indicate Ollama is not responding. Please check the server and try again.", "error")
            return redirect(url_for('scoring.questionnaire_form'))
    
    except TimeoutError as e:
        logger.error(f"AI scoring timeout for user_id={user_id}: {e}", exc_info=True)
        if request.is_json:
            return jsonify({"error": "Scoring request timed out"}), 504
        else:
            flash("Scoring took too long to respond. Please try again later.", "error")
            return redirect(url_for('scoring.questionnaire_form'))
    
    except Exception as e:
        logger.critical(f"Unexpected error in questionnaire submission for user_id={user_id}: {e}", exc_info=True)
        if request.is_json:
            return jsonify({"error": "An unexpected error occurred"}), 500
        else:
            flash("An unexpected error occurred. Please contact support.", "error")
            return redirect(url_for('scoring.questionnaire_form'))


@scoring_bp.route("/api/scoring/profile", methods=["GET"])
@jwt_required()
def get_scoring_profile():
    """
    Get user's scoring profile (roles, interests, motivation).
    
    Response (200):
    {
        "status": "success",
        "data": {
            "dominant_roles": ["Builder", "Problem Solver", "Architect", "Collaborator"],
            "all_roles": {
                "Builder": {"score": 8.5, "is_dominant": true},
                "Architect": {"score": 8.2, "is_dominant": true},
                "Problem Solver": {"score": 8.0, "is_dominant": true},
                "Collaborator": {"score": 7.5, "is_dominant": true},
                "Designer": {"score": 5.2, "is_dominant": false},
                ...
            },
            "motivation_score": 7.5,
            "top_interests": [
                {"name": "Backend Development", "score": 8.2},
                ...
            ],
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    }
    
    Errors:
    - 404: User hasn't completed questionnaire yet
    """
    user_id = get_jwt_identity()  # Convert string to int
    
    from app.models.scoring import UserScoring
    
    scoring = UserScoring.query.filter_by(user_id=user_id).first()
    
    if not scoring:
        return jsonify({
            "error": "Profile not found",
            "message": "Please complete the initial questionnaire first"
        }), 404
    
    # Format all roles with dominant flag
    all_roles = {}
    for role, score in scoring.raw_role_scores.items():
        all_roles[role] = {
            "score": float(score),
            "is_dominant": role in scoring.dominant_roles
        }
    
    return jsonify({
        "status": "success",
        "data": {
            "dominant_roles": scoring.dominant_roles,
            "all_roles": all_roles,
            "motivation_score": float(scoring.motivation_score),
            "top_interests": scoring.get_top_interests(n=10),
            "created_at": scoring.created_at.isoformat(),
            "updated_at": scoring.updated_at.isoformat()
        }
    }), 200


@scoring_bp.route("/api/scoring/history", methods=["GET"])
@jwt_required()
def get_scoring_history():
    """
    Get user's scoring change history.
    
    Query params:
    - limit: Max number of entries to return (default: 20)
    
    Response (200):
    {
        "status": "success",
        "data": {
            "total_count": 5,
            "entries": [
                {
                    "event_type": "project_creation",
                    "event_description": "Created project: AI Chatbot (Python, Flask, NLP)",
                    "summary": "Backend Development ↑0.5, NLP ↑0.3",
                    "created_at": "2024-01-20T15:45:00Z"
                },
                ...
            ]
        }
    }
    """
    user_id = get_jwt_identity()  # Convert string to int
    limit = request.args.get('limit', 20, type=int)
    
    from app.models.scoring_history import ScoringHistory
    
    history_query = (
        ScoringHistory.query
        .filter_by(user_id=user_id)
        .order_by(ScoringHistory.created_at.desc())
        .limit(limit)
    )
    
    entries = []
    for entry in history_query.all():
        entries.append({
            "event_type": entry.event_type,
            "event_description": entry.event_description,
            "summary": entry.get_summary(),
            "created_at": entry.created_at.isoformat()
        })
    
    total_count = ScoringHistory.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        "status": "success",
        "data": {
            "total_count": total_count,
            "entries": entries
        }
    }), 200

@scoring_bp.route("/retake", methods=["POST"])
@jwt_required()
def retake_questionnaire():
    """
    Allow user to retake the questionnaire by deleting their current scores.
    """
    user_id = get_jwt_identity()
    
    from app.models.scoring import UserScoring
    from app.models.scoring_history import ScoringHistory
    from app.models.user import User
    
    logger.info(f"User {user_id} requested to retake questionnaire")
    
    try:
        # Delete existing scoring record
        scoring = UserScoring.query.filter_by(user_id=user_id).first()
        if scoring:
            # Delete all history entries
            ScoringHistory.query.filter_by(user_id=user_id).delete()
            # Delete the scoring record
            db.session.delete(scoring)
            
            # Reset the questionnaire flag
            user = User.query.get(user_id)
            if user:
                user.has_completed_questionnaire = False
            
            db.session.commit()
            logger.info(f"Reset questionnaire for user {user_id}")
            flash("Your profile has been reset. You can now retake the questionnaire.", "success")
        else:
            flash("No profile found to reset.", "info")
        
        return redirect(url_for('scoring.questionnaire_form'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting questionnaire for user {user_id}: {e}", exc_info=True)
        flash("An error occurred while resetting your profile. Please try again.", "error")
        return redirect(url_for('dashboard.profile_page'))