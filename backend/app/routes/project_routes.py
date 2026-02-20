"""
Project Routes

HTTP handling only. No business logic.
Three-step pattern: validate request → call service → return JSON.

Blueprint prefix: /api/projects (registered in app/__init__.py)
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.services.project_service import ProjectService
from app.models.project import ProjectStatus, MembershipPolicy, ProjectVisibility
from app.models.project_member import ProjectMemberRole

logger = logging.getLogger(__name__)

projects_bp = Blueprint("projects", __name__)


# =============================================================================
# HELPERS
# =============================================================================

def _parse_status(value):
    """Safely parse a status string to ProjectStatus enum. Returns None if invalid."""
    if value is None:
        return None
    for member in ProjectStatus:
        if member.value == value:
            return member
    return None


def _parse_policy(value):
    """Safely parse a policy string to MembershipPolicy enum. Returns None if invalid."""
    if value is None:
        return None
    for member in MembershipPolicy:
        if member.value == value:
            return member
    return None


def _parse_visibility(value):
    """Safely parse a visibility string to ProjectVisibility enum. Returns None if invalid."""
    if value is None:
        return None
    for member in ProjectVisibility:
        if member.value == value:
            return member
    return None


def _serialize_project(project):
    """Serialize a Project instance to a JSON-safe dict."""
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "creator_id": project.creator_id,
        "status": project.status.value,
        "membership_policy": project.membership_policy.value,
        "visibility": project.visibility.value,
        "interest_tags": project.interest_tags or [],
        "forked_from_id": project.forked_from_id,
        "fork_count": project.fork_count,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "languages": [
            {"id": pl.language_id, "name": pl.language.name}
            for pl in project.languages
            if pl.language
        ],
        "members": [
            {
                "user_id": pm.user_id,
                "role": pm.role.value,
                "created_at": pm.created_at.isoformat() if pm.created_at else None,
            }
            for pm in project.members
        ]
    }


# =============================================================================
# DISCOVERY
# =============================================================================

@projects_bp.route("", methods=["GET"])
@jwt_required()
def discover_projects():
    """
    GET /api/projects
    Returns ranked list of public projects based on user's interest overlap.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 100)  # Hard cap — prevent abuse

    success, message, results = ProjectService.discover_projects(
        user_id=user_id,
        limit=limit
    )

    if not success:
        logger.error(f"Discovery failed for user_id={user_id}: {message}")
        return jsonify({"success": False, "message": message}), 500

    return jsonify({
        "success": True,
        "data": [
            {
                "project": _serialize_project(r["project"]),
                "overlap_score": r["overlap_score"]
            }
            for r in results
        ],
        "count": len(results)
    }), 200


# =============================================================================
# GET SINGLE PROJECT
# =============================================================================

@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    """
    GET /api/projects/<id>
    Returns full project detail including members and languages.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    from app.models.project import Project

    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"success": False, "message": "Project not found"}), 404

    # Private projects only visible to members
    if project.visibility == ProjectVisibility.PRIVATE:
        is_member = any(pm.user_id == user_id for pm in project.members)
        if not is_member:
            return jsonify({
                "success": False,
                "message": "You do not have access to this project"
            }), 403

    return jsonify({
        "success": True,
        "data": _serialize_project(project)
    }), 200


# =============================================================================
# CREATE PROJECT
# =============================================================================

@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """
    POST /api/projects
    Body (JSON):
        title          (str, required)
        description    (str, optional)
        status         (str, optional) — ProjectStatus value
        membership_policy (str, optional) — MembershipPolicy value
        visibility     (str, optional) — ProjectVisibility value
        interest_tags  (list[str], optional)
        language_ids   (list[int], optional)
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    # Parse enums — reject unknown values explicitly
    status_raw = body.get("status")
    policy_raw = body.get("membership_policy")
    visibility_raw = body.get("visibility")

    data = {
        "title": body.get("title", ""),
        "description": body.get("description"),
        "interest_tags": body.get("interest_tags") or [],
        "language_ids": body.get("language_ids") or [],
    }

    if status_raw is not None:
        parsed = _parse_status(status_raw)
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid status '{status_raw}'. "
                           f"Valid values: {[s.value for s in ProjectStatus]}"
            }), 400
        data["status"] = parsed

    if policy_raw is not None:
        parsed = _parse_policy(policy_raw)
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid membership_policy '{policy_raw}'. "
                           f"Valid values: {[p.value for p in MembershipPolicy]}"
            }), 400
        data["membership_policy"] = parsed

    if visibility_raw is not None:
        parsed = _parse_visibility(visibility_raw)
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid visibility '{visibility_raw}'. "
                           f"Valid values: {[v.value for v in ProjectVisibility]}"
            }), 400
        data["visibility"] = parsed

    success, message, project = ProjectService.create_project(
        creator_id=user_id,
        data=data
    )

    if not success:
        return jsonify({"success": False, "message": message}), 400

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_project(project)
    }), 201


# =============================================================================
# UPDATE PROJECT
# =============================================================================

@projects_bp.route("/<int:project_id>", methods=["PATCH"])
@jwt_required()
def update_project(project_id):
    """
    PATCH /api/projects/<id>
    Partial update. Only provided fields are changed.
    Body (JSON): any subset of create_project fields.
    Status field triggers state machine validation.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    data = {}

    if "title" in body:
        data["title"] = body["title"]
    if "description" in body:
        data["description"] = body["description"]
    if "interest_tags" in body:
        data["interest_tags"] = body["interest_tags"]
    if "language_ids" in body:
        data["language_ids"] = body["language_ids"]

    if "status" in body:
        parsed = _parse_status(body["status"])
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid status '{body['status']}'. "
                           f"Valid values: {[s.value for s in ProjectStatus]}"
            }), 400
        data["status"] = parsed

    if "membership_policy" in body:
        parsed = _parse_policy(body["membership_policy"])
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid membership_policy '{body['membership_policy']}'. "
                           f"Valid values: {[p.value for p in MembershipPolicy]}"
            }), 400
        data["membership_policy"] = parsed

    if "visibility" in body:
        parsed = _parse_visibility(body["visibility"])
        if parsed is None:
            return jsonify({
                "success": False,
                "message": f"Invalid visibility '{body['visibility']}'. "
                           f"Valid values: {[v.value for v in ProjectVisibility]}"
            }), 400
        data["visibility"] = parsed

    success, message, project = ProjectService.update_project(
        project_id=project_id,
        user_id=user_id,
        data=data
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_project(project)
    }), 200


# =============================================================================
# FORK PROJECT
# =============================================================================

@projects_bp.route("/<int:project_id>/fork", methods=["POST"])
@jwt_required()
def fork_project(project_id):
    """
    POST /api/projects/<id>/fork
    No body required.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    success, message, project = ProjectService.fork_project(
        source_project_id=project_id,
        forking_user_id=user_id
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_project(project)
    }), 201


# =============================================================================
# MEMBERSHIP — ADD
# =============================================================================

@projects_bp.route("/<int:project_id>/members", methods=["POST"])
@jwt_required()
def add_member(project_id):
    """
    POST /api/projects/<id>/members
    Body (JSON):
        target_user_id (int, required) — user to add
    Role is determined by project membership_policy — do not pass role.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    target_user_id = body.get("target_user_id")
    if not target_user_id:
        return jsonify({"success": False, "message": "target_user_id is required"}), 400

    success, message, member = ProjectService.add_member(
        project_id=project_id,
        actor_id=user_id,
        target_user_id=target_user_id
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "user_id": member.user_id,
            "role": member.role.value,
            "project_id": member.project_id
        }
    }), 201


# =============================================================================
# MEMBERSHIP — APPROVE OR PROMOTE
# =============================================================================

@projects_bp.route("/<int:project_id>/members/<int:target_user_id>", methods=["PATCH"])
@jwt_required()
def update_member(project_id, target_user_id):
    """
    PATCH /api/projects/<id>/members/<uid>
    Body (JSON):
        action (str, required) — "approve" or "promote"

    approve: PENDING → CONTRIBUTOR
    promote: any role → OWNER
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    action = body.get("action")
    if action not in ("approve", "promote"):
        return jsonify({
            "success": False,
            "message": "action must be 'approve' or 'promote'"
        }), 400

    if action == "approve":
        success, message, member = ProjectService.approve_member(
            project_id=project_id,
            actor_id=user_id,
            pending_user_id=target_user_id
        )
    else:
        success, message, member = ProjectService.promote_to_owner(
            project_id=project_id,
            actor_id=user_id,
            target_user_id=target_user_id
        )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "user_id": member.user_id,
            "role": member.role.value,
            "project_id": member.project_id
        }
    }), 200


# =============================================================================
# MEMBERSHIP — REMOVE
# =============================================================================

@projects_bp.route("/<int:project_id>/members/<int:target_user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(project_id, target_user_id):
    """
    DELETE /api/projects/<id>/members/<uid>
    Owners can remove any member. Members can remove themselves (self-leave).
    Cannot remove last owner.
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    success, message = ProjectService.remove_member(
        project_id=project_id,
        actor_id=user_id,
        target_user_id=target_user_id
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200


# =============================================================================
# DELETE PROJECT (SOFT — sets status to CANCELLED)
# =============================================================================

@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """
    DELETE /api/projects/<id>
    Soft delete — sets status to CANCELLED via state machine.
    Only owners can cancel a project.
    COMPLETED projects cannot be cancelled (state machine enforced).
    """
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid token identity'}), 401

    success, message, project = ProjectService.update_project(
        project_id=project_id,
        user_id=user_id,
        data={"status": ProjectStatus.CANCELLED}
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": "Project cancelled successfully"}), 200
