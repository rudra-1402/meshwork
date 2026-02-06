from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.services.community_service import create_community_service
from app.models.community import Community
from app.models.community_member import CommunityMember

community_routes = Blueprint(
    "community_routes",
    __name__,
    url_prefix="/communities"
)

# ================= CREATE COMMUNITY =================
@community_routes.route("/create", methods=["GET", "POST"])
@login_required
def create_community():
    if request.method == "POST":
        community_name = request.form.get("community_name")
        subject = request.form.get("subject")

        if not community_name or not subject:
            flash("All fields are required")
            return redirect(url_for("community_routes.create_community"))

        create_community_service(
            community_name=community_name,
            subject=subject,
            college_id=current_user.college_id,
            user_id=current_user.id
        )

        flash("Community created successfully")
        return redirect(url_for("dashboard_routes.dashboard"))

    return render_template("communities/create_community.html")


# ================= EXPLORE COMMUNITIES =================
@community_routes.route("/explore")
@login_required
def explore_communities():
    # All communities of user's college
    communities = Community.query.filter_by(
        college_id=current_user.college_id
    ).all()

    # Community IDs that current user has joined
    joined_ids = {
        member.community_id
        for member in CommunityMember.query.filter_by(
            user_id=current_user.id
        ).all()
    }

    return render_template(
        "communities/explore_communities.html",
        communities=communities,
        joined_ids=joined_ids
    )


# ================= JOIN COMMUNITY =================
@community_routes.route("/join/<int:community_id>", methods=["POST"])
@login_required
def join_community(community_id):
    # Prevent duplicate join
    existing_member = CommunityMember.query.filter_by(
        user_id=current_user.id,
        community_id=community_id
    ).first()

    if not existing_member:
        member = CommunityMember(
            user_id=current_user.id,
            community_id=community_id
        )
        db.session.add(member)
        db.session.commit()
        flash("You joined the community successfully")

    return redirect(url_for("community_routes.explore_communities"))
