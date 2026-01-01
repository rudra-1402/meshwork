from flask import Blueprint, render_template, request, redirect, url_for, session

auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == "test@example.com" and password == "1234":
            session["user_id"] = 1
            session["user_email"] = email

            return redirect(url_for("dashboard_routes.dashboard"))
        else:
            return render_template("auth/login.html", error = "Invalid Credentials")

        return render_template("auth/login.html")
    return render_template("auth/login.html")

@auth_routes.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main_routes.landing"))