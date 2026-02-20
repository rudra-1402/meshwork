from app.extensions import db
from app.models.user import User
from sqlalchemy.exc import IntegrityError


def get_user_by_email(email):
    """
    Fetch a user by email address.
    
    Args:
        email (str): User's email address
    
    Returns:
        User: User object if found, None otherwise
    """
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    """
    Fetch a user by their unique ID.
    
    Args:
        user_id (int): User's unique identifier
    
    Returns:
        User: User object if found, None otherwise
    """
    return db.session.get(User, user_id)


def create_user(username, first_name, last_name, email, password, college_id=None):
    """
    Create and persist a new user account.
    
    Args:
        username (str): Desired username (must be unique)
        first_name (str): User's first name
        last_name (str): User's last name
        email (str): User's email address (must be unique)
        password (str): Plain text password (will be hashed automatically)
        college_id (int, optional): Associated college ID. Defaults to None.
    
    Returns:
        User: Created user object with gamification fields initialized:
              - xp = 0, level = 1, reputation = 0
              - current_streak = 0, max_streak = 0
        None: If user already exists (duplicate email or username)
    
    Note:
        Gamification fields are automatically initialized with defaults.
        Password is hashed using User.set_password() before storage.
    """
    # Check if username is taken
    if User.query.filter_by(username=username).first():
        return None
    
    # Check if email is taken
    if User.query.filter_by(email=email).first():
        return None
    
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
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


def check_username_availability(username):
    """
    Check if username is available.
    
    Args:
        username (str): Username to check
    
    Returns:
        bool: True if available, False if taken
    """
    return User.query.filter_by(username=username).first() is None


def authenticate_user(email, password):
    """
    Authenticate user credentials.
    
    Args:
        email (str): User's email address
        password (str): Plain text password to verify
    
    Returns:
        dict: Authentication result with keys:
            - success (bool): True if authentication successful
            - user (User|None): User object if successful, None otherwise
            - message (str|None): Error message if failed, None if successful
    
    Example:
        >>> result = authenticate_user('user@example.com', 'password123')
        >>> if result['success']:
        ...     user = result['user']
        ...     # Process successful login
        >>> else:
        ...     print(result['message'])  # "Invalid email or password"
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
