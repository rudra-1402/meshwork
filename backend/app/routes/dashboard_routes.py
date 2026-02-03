from flask import Blueprint, render_template, session, redirect, url_for

dashboard_routes = Blueprint("dashboard_routes", __name__)

@dashboard_routes.route("/dashboard")
def dashboard():
    # User logged in
    if session.get("user_id"):
        return render_template("dashboard/dashboard.html", role="user")

    # College logged in
    if session.get("college_id"):
        return render_template("dashboard/dashboard.html", role="college")

    # ❌ OLD (WRONG)
    # return redirect(url_for("auth_routes.login"))

    # ✅ NEW (CORRECT)
    return redirect(url_for("auth_routes.user_login"))
