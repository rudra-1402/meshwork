from flask import Blueprint, render_template, session, redirect, url_for

dashboard_routes = Blueprint("dashboard_routes", __name__)

@dashboard_routes.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth_routes.login"))
    else:
        return render_template("dashboard/dashboard.html", email=session.get("user_email"))