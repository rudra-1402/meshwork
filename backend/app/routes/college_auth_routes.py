from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.college_auth_services import authenticate_college, create_college
from flask_jwt_extended import create_access_token, unset_jwt_cookies, set_access_cookies

college_auth_routes = Blueprint("college_auth", __name__)

# ================= COLLEGE LOGIN =================
@college_auth_routes.route("/login/college", methods=["GET", "POST"])
def college_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        result = authenticate_college(email, password)

        if result["success"]:
            college = result["college"]

            # Create JWT access token with college ID (prefixed with 'college_')
            access_token = create_access_token(identity=f"college_{college.id}")
            
            # Store token in HTTP-only cookie
            response = redirect(url_for("dashboard.college_dashboard"))
            set_access_cookies(response, access_token)

            flash("College logged in successfully!", "success")
            return response

        flash(result["message"], "error")
        return redirect(url_for("college_auth.college_login"))

    return render_template("colleges/login_college.html")


# ================= COLLEGE SIGNUP =================
@college_auth_routes.route("/signup/college", methods=["GET", "POST"])
def college_signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        city = request.form.get("city")
        state = request.form.get("state")

        # ---- validations ----
        if not name or not email or not password or not confirm_password:
            flash("All fields are required", "error")
            return redirect(url_for("college_auth.college_signup"))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("college_auth.college_signup"))

        college = create_college(
            name=name,
            email=email,
            password=password,
            city=city,
            state=state
        )

        if not college:
            flash("College already exists", "error")
            return redirect(url_for("college_auth.college_signup"))

        flash("College account created! Please login.", "success")
        return redirect(url_for("college_auth.college_login"))

    return render_template("colleges/signup_college.html")

# ================= COLLEGE LOGOUT =================
@college_auth_routes.route("/logout/college")
def college_logout():
    response = redirect(url_for("main_routes.landing"))
    unset_jwt_cookies(response)  # Clear JWT cookies
    flash("College logged out", "success")
    return response
