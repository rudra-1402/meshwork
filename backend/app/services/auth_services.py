from app.extensions import db
from app.models.user import User
from sqlalchemy.exc import IntegrityError


def get_user_by_email(email):
    """
    Fetch a user by email.
    Returns:
        User object or None
    """
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    """
    Fetch a user by ID.
    Returns:
        User object or None
    """
    return User.query.get(user_id)


def create_user(username, email, password, college_id=None):
    """
    Create and persist a new user.
    Returns:
        User object on success
        None on failure (e.g. duplicate email)
    """
    user = User(
        username=username,
        email=email,
        college_id=college_id,
        # is_email_verified=False
    )

    # hash password using model method
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        return user

    except IntegrityError as e:
        db.session.rollback()
        return None


def authenticate_user(email, password):
    """
    Authenticate user credentials.
    Returns:
        dict with keys:
        - success (bool)
        - user (User | None)
        - message (str | None)
    """
    user = get_user_by_email(email)

    if not user:
        return {
            "success": False,
            "user": None,
            "message": "Invalid email or password"
        }

    if not user.check_password(password):
        return {
            "success": False,
            "user": None,
            "message": "Invalid email or password"
        }

    return {
        "success": True,
        "user": user,
        "message": None
    }
