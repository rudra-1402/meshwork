from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import logging

from app.extensions import db
from app.services.scoring_service import ScoringService
from app.exceptions import (
    ValidationError,
    AlreadyScoredError,
    ScoringError,
    NotScoredError
)
from app.utils.jwt_helpers import get_user_id_or_error

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
    Return questionnaire status for users who haven't completed it.
    SPA uses this to decide whether to show the questionnaire form.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    from app.models.scoring import UserScoring

    existing_scoring = UserScoring.query.filter_by(user_id=user_id).first()
    if existing_scoring:
        return jsonify({"success": True, "questionnaire_completed": True}), 200

    return jsonify({"success": True, "questionnaire_completed": False}), 200

@scoring_bp.route("/submit", methods=["POST"])
@jwt_required()
def submit_questionnaire():
    """
    Submit questionnaire — JSON only.
    """
    user_id, error = get_user_id_or_error()
    if error:
        return error
    logger.info(f"=== Starting questionnaire submission for user_id={user_id} ===")

    data = request.get_json(silent=True) or {}
    responses = data.get("responses", {})

    if not responses:
        logger.warning(f"No responses provided for user_id={user_id}")
        return jsonify({"error": "Missing 'responses' field"}), 400

    logger.info(f"Received questionnaire submission for user_id={user_id}")

    try:
        scoring_service = get_scoring_service()
        logger.info(f"Starting AI scoring for user_id={user_id}")

        import signal
        import platform

        def timeout_handler(signum, frame):
            raise TimeoutError("AI scoring exceeded 30 second timeout")

        if platform.system() != 'Windows':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)

        try:
            result = scoring_service.process_initial_questionnaire(user_id, responses)
        finally:
            if platform.system() != 'Windows':
                signal.alarm(0)

        logger.info(f"AI scoring completed for user_id={user_id}: {result}")
        return jsonify({
            "status": "success",
            "message": "Profile completed successfully",
            "data": result
        }), 200

    except AlreadyScoredError as e:
        logger.warning(f"Duplicate questionnaire submission attempt by user_id={user_id}")
        return jsonify({"error": "Questionnaire already submitted", "message": str(e)}), 409

    except ValidationError as e:
        logger.warning(f"Questionnaire validation failed for user_id={user_id}: {e}")
        return jsonify({"error": "Invalid questionnaire data", "message": str(e)}), 400

    except ScoringError as e:
        logger.error(f"AI scoring failed for user_id={user_id}: {e}", exc_info=True)
        return jsonify({"error": "Scoring service temporarily unavailable"}), 503

    except TimeoutError as e:
        logger.error(f"AI scoring timeout for user_id={user_id}: {e}", exc_info=True)
        return jsonify({"error": "Scoring request timed out"}), 504

    except Exception as e:
        logger.critical(f"Unexpected error in questionnaire submission for user_id={user_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@scoring_bp.route("/profile", methods=["GET"])
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
    user_id, error = get_user_id_or_error()
    if error:
        return error

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


@scoring_bp.route("/history", methods=["GET"])
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
    user_id, error = get_user_id_or_error()
    if error:
        return error
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
    user_id, error = get_user_id_or_error()
    if error:
        return error

    from app.models.scoring import UserScoring
    from app.models.scoring_history import ScoringHistory
    from app.models.user import User

    logger.info(f"User {user_id} requested to retake questionnaire")

    try:
        scoring = UserScoring.query.filter_by(user_id=user_id).first()
        if scoring:
            ScoringHistory.query.filter_by(user_id=user_id).delete()
            db.session.delete(scoring)

            user = db.session.get(User, user_id)
            if user:
                user.has_completed_questionnaire = False

            db.session.commit()
            logger.info(f"Reset questionnaire for user {user_id}")

        return jsonify({
            "success": True,
            "message": "Profile reset. You may retake the questionnaire."
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting questionnaire for user {user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "message": "An error occurred while resetting your profile."}), 500