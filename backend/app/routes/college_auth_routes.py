from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.college_auth_services import authenticate_college, create_college

college_auth_routes = Blueprint("college_auth_routes", __name__)

# ================= COLLEGE LOGIN =================
@college_auth_routes.route("/login/college", methods=["GET", "POST"])
def college_login():
    if request.method == "POST":
        # LOGIN USING COLLEGE NAME
        name = request.form.get("name")
        password = request.form.get("password")

        result = authenticate_college(name, password)

        if result["success"]:
            college = result["college"]

            # create session
            session.clear()
            session["college_id"] = college.id

            flash("College logged in successfully!", "success")

            # ✅ REDIRECT TO NEW HOME PAGE
            return redirect(url_for("college_home_routes.college_home"))

        flash(result["message"], "error")
        return redirect(url_for("college_auth_routes.college_login"))

    return render_template("colleges/login_college.html")


# ================= COLLEGE SIGNUP =================
@college_auth_routes.route("/signup/college", methods=["GET", "POST"])
def college_signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        position = request.form.get("position")

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([
            name, email, city, state, address,
            first_name, last_name, position,
            password, confirm_password
        ]):
            flash("All fields are required", "error")
            return redirect(url_for("college_auth_routes.college_signup"))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("college_auth_routes.college_signup"))

        result = create_college(
            name=name,
            email=email,
            city=city,
            state=state,
            first_name=first_name,
            last_name=last_name,
            position=position,
            address=address,
            password=password
        )

        if not result["success"]:
            flash(result["message"], "error")
            return redirect(url_for("college_auth_routes.college_signup"))

        flash("College registered successfully! Please login.", "success")
        return redirect(url_for("college_auth_routes.college_login"))

    return render_template("colleges/signup_college.html")


# ================= COLLEGE LOGOUT =================
@college_auth_routes.route("/logout/college")
def college_logout():
    session.clear()
    flash("College logged out", "success")
    return redirect(url_for("college_auth_routes.college_login"))
