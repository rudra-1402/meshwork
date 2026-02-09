from flask import Blueprint, render_template, session, redirect, url_for

college_home_routes = Blueprint("college_home_routes", __name__)

@college_home_routes.route("/college/home")
def college_home():
    if "college_id" not in session:
        return redirect(url_for("college_auth_routes.college_login"))

    # ✅ FIXED TEMPLATE PATH
    return render_template("colleges/home.html")
