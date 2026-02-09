from app.extensions import db
from app.models.college import College
from sqlalchemy.exc import IntegrityError


def get_college_by_email(email):
    """
    Fetch a college by email address.
    
    Args:
        email (str): College's email address
    
    Returns:
        College: College object if found, None otherwise
    """
    return College.query.filter_by(email=email).first()


def get_college_by_id(college_id):
    """
    Fetch a college by its unique ID.
    
    Args:
        college_id (int): College's unique identifier
    
    Returns:
        College: College object if found, None otherwise
    """
    return College.query.get(college_id)


def create_college(name, email, password, city=None, state=None):
    """
    Create and persist a new college account.
    
    Args:
        name (str): College name
        email (str): College's email address (must be unique)
        password (str): Plain text password (will be hashed automatically)
        city (str, optional): College city. Defaults to None.
        state (str, optional): College state. Defaults to None.
    
    Returns:
        College: Created college object on success
        None: If college already exists (duplicate email)
    
    Note:
        Password is hashed using College.set_password() before storage.
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
    """
    Authenticate college credentials.
    
    Args:
        email (str): College's email address
        password (str): Plain text password to verify
    
    Returns:
        dict: Authentication result with keys:
            - success (bool): True if authentication successful
            - college (College|None): College object if successful, None otherwise
            - message (str|None): Error message if failed, None if successful
    
    Example:
        >>> result = authenticate_college('college@example.edu', 'password123')
        >>> if result['success']:
        ...     college = result['college']
        ...     # Process successful login
        >>> else:
        ...     print(result['message'])  # "Invalid email or password"
    """
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
