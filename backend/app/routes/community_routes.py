from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.community_service import create_community_service
from app.models.community import Community
from flask_login import login_required, current_user

community_routes = Blueprint(
    "community_routes",
    __name__,
    url_prefix="/communities"
)


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


@community_routes.route("/explore")
@login_required
def explore_communities():
    communities = Community.query.filter_by(
        college_id=current_user.college_id
    ).all()

    return render_template(
        "communities/explore_communities.html",
        communities=communities
    )
