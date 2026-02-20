from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.services.community_service import CommunityService
from app.services.auth_services import get_user_by_id
from app.models.community import Community
from app.models.community_member import CommunityMember
from app.models.community_message import CommunityMessage
from app.utils.jwt_helpers import get_user_id_or_error

community_routes = Blueprint(
    "community_routes",
    __name__
)


# ================= CREATE COMMUNITY =================
@community_routes.route("/create", methods=["POST"])
@jwt_required()
def create_community():
    user_id, err = get_user_id_or_error()
    if err:
        return err

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    community_name = data.get("community_name")
    subject = data.get("subject")

    if not community_name or not subject:
        return jsonify({"success": False, "message": "community_name and subject are required"}), 400

    community = CommunityService.create_community(
        community_name=community_name,
        subject=subject,
        college_id=user.college_id,
        user_id=user.id
    )

    return jsonify({
        "success": True,
        "community": {
            "community_id": community.community_id,
            "community_name": community.community_name,
            "subject": community.subject,
            "college_id": community.college_id,
            "created_by": community.created_by,
        }
    }), 201


# ================= EXPLORE COMMUNITIES =================
@community_routes.route("/explore")
@jwt_required()
def explore_communities():
    user_id, err = get_user_id_or_error()
    if err:
        return err

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    communities = Community.query.filter_by(college_id=user.college_id).all()

    joined_ids = {
        member.community_id
        for member in CommunityMember.query.filter_by(user_id=user.id).all()
    }

    return jsonify({
        "success": True,
        "communities": [
            {
                "community_id": c.community_id,
                "community_name": c.community_name,
                "subject": c.subject,
                "is_member": c.community_id in joined_ids,
            }
            for c in communities
        ]
    }), 200


# ================= JOIN COMMUNITY =================
@community_routes.route("/join/<int:community_id>", methods=["POST"])
@jwt_required()
def join_community(community_id):
    user_id, err = get_user_id_or_error()
    if err:
        return err

    joined, message = CommunityService.join_community(community_id, user_id)
    if joined:
        return jsonify({"success": True, "message": message}), 200
    return jsonify({"success": False, "message": message}), 400


# ================= VIEW COMMUNITY =================
@community_routes.route("/view/<int:community_id>")
@jwt_required()
def view_community(community_id):
    user_id, err = get_user_id_or_error()
    if err:
        return err

    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"success": False, "message": "Community not found"}), 404

    is_member = CommunityMember.query.filter_by(
        user_id=user_id,
        community_id=community_id
    ).first()
    if not is_member:
        return jsonify({"success": False, "message": "Join the community to view messages."}), 403

    messages = (
        CommunityMessage.query
        .filter_by(community_id=community_id)
        .order_by(CommunityMessage.messaged_at.asc())
        .all()
    )

    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))

    return jsonify({
        "success": True,
        "community": {
            "community_id": community.community_id,
            "community_name": community.community_name,
            "subject": community.subject,
            "is_admin": is_admin,
        },
        "messages": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "message": m.message,
                "messaged_at": m.messaged_at.isoformat() if m.messaged_at else None,
            }
            for m in messages
        ]
    }), 200


# ================= SEND MESSAGE (ADMIN) =================
@community_routes.route("/message/<int:community_id>", methods=["POST"])
@jwt_required()
def send_message(community_id):
    user_id, err = get_user_id_or_error()
    if err:
        return err

    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"success": False, "message": "Community not found"}), 404

    if community.created_by != user_id:
        return jsonify({"success": False, "message": "Only the community admin can send messages."}), 403

    data = request.get_json(silent=True) or {}
    message_text = data.get("message", "").strip()
    if not message_text:
        return jsonify({"success": False, "message": "Message cannot be empty."}), 400

    success, msg_result, msg_obj = CommunityService.send_message(community_id, user_id, message_text)
    if success:
        return jsonify({
            "success": True,
            "message": {
                "id": msg_obj.id if msg_obj else None,
                "text": msg_result,
            }
        }), 201
    return jsonify({"success": False, "message": msg_result}), 400


# ================= CREATE TASK (ADMIN) =================
@community_routes.route("/<int:community_id>/tasks/create", methods=["POST"])
@jwt_required()
def create_task(community_id):
    import json as _json

    user_id, err = get_user_id_or_error()
    if err:
        return err

    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"success": False, "message": "Community not found"}), 404

    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))

    if not is_admin:
        return jsonify({"success": False, "message": "Only admins can create tasks."}), 403

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    difficulty = data.get("difficulty", "Medium")
    max_xp = data.get("max_xp_reward", 0)
    actions = data.get("actions", [])

    if not title:
        return jsonify({"success": False, "message": "Task title is required."}), 400

    success, msg, task = CommunityService.create_task(
        community_id=community_id,
        user_id=user_id,
        title=title,
        description=description,
        actions=actions,
        difficulty=difficulty,
        max_xp_reward=max_xp
    )

    if success:
        return jsonify({
            "success": True,
            "task": {
                "task_id": task.task_id if task else None,
                "title": title,
                "difficulty": difficulty,
            }
        }), 201
    return jsonify({"success": False, "message": msg}), 400


# ================= VIEW TASKS =================
@community_routes.route("/<int:community_id>/tasks", methods=["GET"])
@jwt_required()
def view_tasks(community_id):
    from app.models.community_task import CommunityTask

    user_id, err = get_user_id_or_error()
    if err:
        return err

    community = db.session.get(Community, community_id)
    if not community:
        return jsonify({"success": False, "message": "Community not found"}), 404

    tasks = CommunityTask.query.filter_by(community_id=community_id).all()

    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))

    return jsonify({
        "success": True,
        "is_admin": is_admin,
        "tasks": [
            {
                "task_id": t.task_id,
                "title": t.title,
                "description": t.description,
                "difficulty": t.difficulty,
                "max_xp_reward": t.max_xp_reward,
                "is_active": t.is_active,
            }
            for t in tasks
        ]
    }), 200
