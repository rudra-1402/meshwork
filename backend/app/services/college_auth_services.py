from app.extensions import db
from app.models.college import College
from sqlalchemy.exc import IntegrityError


def get_college_by_email(email):
    return College.query.filter_by(email=email).first()


def create_college(name, email, password, city=None, state=None):
    """
    Create and persist a new college
    """
    college = College(
        name=name,
        email=email,
        city=city,
        state=state
    )

    # hash password
    college.set_password(password)

    try:
        db.session.add(college)
        db.session.commit()
        return college

    except IntegrityError:
        db.session.rollback()
        return None


def authenticate_college(email, password):
    college = get_college_by_email(email)

    if not college:
        return {
            "success": False,
            "college": None,
            "message": "Invalid email or password"
        }

    if not college.check_password(password):
        return {
            "success": False,
            "college": None,
            "message": "Invalid email or password"
        }

    return {
        "success": True,
        "college": college,
        "message": None
    }
