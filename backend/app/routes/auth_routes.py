from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_services import authenticate_user, create_user
from app.utils.validators import is_empty, is_valid_email
from app.models.college import College

auth_routes = Blueprint("auth_routes", __name__)

# ================= USER LOGIN =================
@auth_routes.route("/login/user", methods=["GET", "POST"])
def user_login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # ---- validations ----
        if is_empty(email) or is_empty(password):
            flash("Email and password are required.", "error")
            return redirect(url_for("auth_routes.user_login"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth_routes.user_login"))

        result = authenticate_user(email, password)

        if result["success"]:
            user = result["user"]

            session.clear()
            session["user_id"] = user.id
            session["user_email"] = user.email

            flash("Logged in successfully!", "success")

            # 🔥 If user has not completed onboarding → ask questions
            if not user.interests or len(user.interests) == 0:
                return redirect(url_for("onboarding_routes.onboarding"))

            return redirect(url_for("dashboard_routes.dashboard"))

        flash(result["message"], "error")
        return redirect(url_for("auth_routes.user_login"))

    return render_template("auth/login_user.html")


# ================= USER SIGNUP =================
@auth_routes.route("/signup/user", methods=["GET", "POST"])
def user_signup():

    # 🔹 fetch colleges for dropdown
    colleges = College.query.order_by(College.name).all()

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        college_id = request.form.get("college_id")

        # ---- validations ----
        if (
            is_empty(username)
            or is_empty(email)
            or is_empty(password)
            or is_empty(confirm_password)
            or is_empty(college_id)
        ):
            flash("All fields including college are required.", "error")
            return redirect(url_for("auth_routes.user_signup"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth_routes.user_signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth_routes.user_signup"))

        # 🔥 Create user WITH college_id
        user = create_user(
            username=username,
            email=email,
            password=password,
            college_id=int(college_id)
        )

        if not user:
            flash("Account with this email already exists.", "error")
            return redirect(url_for("auth_routes.user_signup"))

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth_routes.user_login"))

    return render_template(
        "auth/signup_user.html",
        colleges=colleges
    )


# ================= USER LOGOUT =================
@auth_routes.route("/logout/user")
def user_logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main_routes.landing"))
