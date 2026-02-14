from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.services.community_service import create_community_service
from app.services.auth_services import get_user_by_id
from app.models.community import Community
from app.models.community_member import CommunityMember
from app.models.community_message import CommunityMessage
from app.utils.jwt_helpers import get_user_id_or_redirect

community_routes = Blueprint(
    "community_routes",
    __name__,
    url_prefix="/communities"
)


# ================= CREATE COMMUNITY =================
@community_routes.route("/create", methods=["GET", "POST"])
@jwt_required()
def create_community():
    user_id, response = get_user_id_or_redirect()
    if response:
        return response
    user = get_user_by_id(user_id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.user_login"))

    if request.method == "POST":
        community_name = request.form.get("community_name")
        subject = request.form.get("subject")

        if not community_name or not subject:
            flash("All fields are required")
            return redirect(url_for("community_routes.create_community"))

        create_community_service(
            community_name=community_name,
            subject=subject,
            college_id=user.college_id,
            user_id=user.id
        )

        flash("Community created successfully")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("communities/create_community.html")


# ================= EXPLORE COMMUNITIES =================
@community_routes.route("/explore")
@jwt_required()
def explore_communities():
    user_id, response = get_user_id_or_redirect()
    if response:
        return response
    user = get_user_by_id(user_id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.user_login"))

    # All communities of user's college
    communities = Community.query.filter_by(
        college_id=user.college_id
    ).all()

    # Community IDs that current user has joined
    joined_ids = {
        member.community_id
        for member in CommunityMember.query.filter_by(
            user_id=user.id
        ).all()
    }

    return render_template(
        "communities/explore_communities.html",
        communities=communities,
        joined_ids=joined_ids
    )


# ================= JOIN COMMUNITY =================
@community_routes.route("/join/<int:community_id>", methods=["POST"])
@jwt_required()
def join_community(community_id):
    user_id, response = get_user_id_or_redirect()
    if response:
        return response

    # Prevent duplicate join
    existing_member = CommunityMember.query.filter_by(
        user_id=user_id,
        community_id=community_id
    ).first()

    if not existing_member:
        member = CommunityMember(
            user_id=user_id,
            community_id=community_id
        )
        db.session.add(member)
        db.session.commit()
        flash("You joined the community successfully")

    return redirect(url_for("community_routes.explore_communities"))


# ================= VIEW COMMUNITY =================
@community_routes.route("/view/<int:community_id>")
@jwt_required()
def view_community(community_id):
    user_id, response = get_user_id_or_redirect()
    if response:
        return response

    community = Community.query.get(community_id)
    if not community:
        flash("Community not found", "error")
        return redirect(url_for("community_routes.explore_communities"))

    is_member = CommunityMember.query.filter_by(
        user_id=user_id,
        community_id=community_id
    ).first()
    if not is_member:
        flash("Join the community to view messages.", "error")
        return redirect(url_for("community_routes.explore_communities"))

    messages = (
        CommunityMessage.query
        .filter_by(community_id=community_id)
        .order_by(CommunityMessage.messaged_at.asc())
        .all()
    )

    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))

    return render_template(
        "communities/view_communites.html",
        community=community,
        messages=messages,
        is_admin=is_admin
    )


# ================= SEND MESSAGE (ADMIN) =================
@community_routes.route("/message/<int:community_id>", methods=["POST"])
@jwt_required()
def send_message(community_id):
    user_id, response = get_user_id_or_redirect()
    if response:
        return response

    community = Community.query.get(community_id)
    if not community:
        flash("Community not found", "error")
        return redirect(url_for("community_routes.explore_communities"))

    if community.created_by != user_id:
        flash("Only the community admin can send messages.", "error")
        return redirect(url_for("community_routes.view_community", community_id=community_id))

    message_text = request.form.get("message", "").strip()
    if not message_text:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("community_routes.view_community", community_id=community_id))

    message = CommunityMessage(
        user_id=user_id,
        community_id=community_id,
        message=message_text
    )
    db.session.add(message)
    db.session.commit()
    flash("Message sent successfully")

    return redirect(url_for("community_routes.view_community", community_id=community_id))


# ================= CREATE TASK (ADMIN) =================
@community_routes.route("/<int:community_id>/tasks/create", methods=["GET", "POST"])
@jwt_required()
def create_task(community_id):
    from app.models.community_task import CommunityTask
    
    user_id, response = get_user_id_or_redirect()
    if response:
        return response

    community = Community.query.get(community_id)
    if not community:
        flash("Community not found", "error")
        return redirect(url_for("community_routes.explore_communities"))

    # Check if user is community admin or has admin privileges
    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))
    
    if not is_admin:
        flash("Only admins can create tasks.", "error")
        return redirect(url_for("community_routes.view_community", community_id=community_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        difficulty = request.form.get("difficulty", "Medium")
        max_xp = request.form.get("max_xp_reward", 0, type=int)
        
        # Get actions from form (expecting JSON array or comma-separated list)
        actions_raw = request.form.get("actions", "[]")
        try:
            import json
            actions = json.loads(actions_raw)
        except:
            # Fallback: split by newlines if not JSON
            actions_list = [a.strip() for a in actions_raw.split('\n') if a.strip()]
            actions = [{"id": i+1, "text": text, "xp": max_xp // len(actions_list) if actions_list else 0} 
                      for i, text in enumerate(actions_list)]

        if not title:
            flash("Task title is required.", "error")
            return redirect(url_for("community_routes.create_task", community_id=community_id))

        new_task = CommunityTask(
            community_id=community_id,
            created_by=user_id,
            title=title,
            description=description,
            difficulty=difficulty,
            max_xp_reward=max_xp,
            actions=actions
        )
        db.session.add(new_task)
        db.session.commit()
        
        flash(f"Task '{title}' created successfully!", "success")
        return redirect(url_for("community_routes.view_community", community_id=community_id))

    return render_template(
        "communities/create_task.html",
        community=community
    )


# ================= VIEW TASKS (ADMIN) =================
@community_routes.route("/<int:community_id>/tasks", methods=["GET"])
@jwt_required()
def view_tasks(community_id):
    from app.models.community_task import CommunityTask
    
    user_id, response = get_user_id_or_redirect()
    if response:
        return response

    community = Community.query.get(community_id)
    if not community:
        flash("Community not found", "error")
        return redirect(url_for("community_routes.explore_communities"))

    # Get all tasks for this community
    tasks = CommunityTask.query.filter_by(community_id=community_id).all()
    
    # Check if user is admin
    user = get_user_by_id(user_id)
    is_admin = community.created_by == user_id or (user and getattr(user, 'is_admin', False))

    return render_template(
        "communities/view_tasks.html",
        community=community,
        tasks=tasks,
        is_admin=is_admin
    )
