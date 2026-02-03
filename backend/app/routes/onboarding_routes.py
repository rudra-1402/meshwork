from flask import Blueprint, request, redirect, url_for
from app.models.user import User
from app.models.interest import Interest
from app.extensions import db
from app.services.ai_interest_service import detect_interests

onboarding_routes = Blueprint("onboarding_routes", __name__)

@onboarding_routes.route("/onboarding", methods=["POST"])
def onboarding():
    user_id = request.form["user_id"]
    user = User.query.get(user_id)

    answers = dict(request.form)

    ai_interests = detect_interests(answers)

    for name in ai_interests:
        interest = Interest.query.filter_by(name=name).first()
        if not interest:
            interest = Interest(name=name)
            db.session.add(interest)
        user.interests.append(interest)

    db.session.commit()
    return redirect(url_for("dashboard_routes.dashboard"))
