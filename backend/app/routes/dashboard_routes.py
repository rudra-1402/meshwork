from flask import Blueprint, render_template, session, redirect, url_for
from app.utils.decorators import login_required

dashboard_routes = Blueprint("dashboard_routes", __name__)

@dashboard_routes.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard/dashboard.html", email=session.get("user_email"))