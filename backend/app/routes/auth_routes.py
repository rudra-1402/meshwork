from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_services import authenticate_user, create_user
from app.utils.validators import is_empty, is_valid_email

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if is_empty(email) or is_empty(password):
            flash("Email and password are required.", "error")
            return redirect(url_for("auth_routes.login"))

        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth_routes.login"))

        result = authenticate_user(email, password)

        if result["success"]:
            user = result["user"]
            session["user_id"] = user.id
            session["user_email"] = user.email
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard_routes.dashboard"))

        flash(result["message"], "error")
        return redirect(url_for("auth_routes.login"))

    return render_template("auth/login.html")

@auth_routes.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # basic validations
        if is_empty(username) or is_empty(email) or is_empty(password) or is_empty(confirm_password):
            flash("All fields are required.", "error")
            return redirect(url_for("auth_routes.signup"))
        if not is_valid_email(email):
            flash("Invalid email format.", "error")
            return redirect(url_for("auth_routes.signup"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth_routes.signup"))
        
        # Create user
        user = create_user(
                username=username,
                email=email,
                password=password
            )
        if not user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("auth_routes.signup"))
        
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth_routes.login"))

    return render_template("auth/signup.html")
@auth_routes.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main_routes.landing"))