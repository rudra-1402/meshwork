from flask import Blueprint, render_template, request, redirect, url_for, session
from app.services.ai_interest_service import detect_interests

onboarding_routes = Blueprint("onboarding_routes", __name__)

@onboarding_routes.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if "user_id" not in session:
        return redirect(url_for("auth_routes.user_login"))

    if request.method == "POST":
        answers = request.form.to_dict(flat=False)

        interests = detect_interests(answers)

        session["detected_interests"] = interests

        return redirect(url_for("onboarding_routes.interest_result"))

    return render_template("onboarding.html")


@onboarding_routes.route("/interest-result")
def interest_result():
    interests = session.get("detected_interests", [])
    return render_template("interest_result.html", interests=interests)
