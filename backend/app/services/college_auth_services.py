from app.extensions import db
from app.models.college import College
from sqlalchemy.exc import IntegrityError


def get_college_by_name(name):
    return College.query.filter_by(name=name).first()


def get_college_by_email(email):
    return College.query.filter_by(email=email).first()


def get_college_by_id(college_id):
    return College.query.get(college_id)


def create_college(
    name,
    email,
    city,
    state,
    first_name,
    last_name,
    position,
    address,
    password
):
    if get_college_by_name(name):
        return {"success": False, "message": "College name already exists"}

    if get_college_by_email(email):
        return {"success": False, "message": "Email domain already registered"}

    college = College(
        name=name,
        email=email,
        city=city,
        state=state,
        first_name=first_name,
        last_name=last_name,
        position=position,
        address=address
    )

    college.set_password(password)

    try:
        db.session.add(college)
        db.session.commit()
        return {"success": True, "college": college}
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "message": "College already exists"}


# 🔥 UPDATED LOGIN FUNCTION
def authenticate_college(name, password):
    college = get_college_by_name(name)

    if not college or not college.check_password(password):
        return {
            "success": False,
            "college": None,
            "message": "Invalid college name or password"
        }

    return {
        "success": True,
        "college": college,
        "message": None
    }
