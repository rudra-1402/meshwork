from app.extensions import db
from app.models.college import College
from sqlalchemy.exc import IntegrityError
import re


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
    return db.session.get(College, college_id)


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


def get_college_email_configuration(college_id):
    """
    Get a college's email-domain and pattern configuration.
    """
    college = get_college_by_id(college_id)
    if not college:
        return False, "College not found", None

    return True, None, {
        "college_id": college.id,
        "domain": college.domain,
        "student_email_pattern": college.student_email_pattern,
        "personnel_email_pattern": college.personnel_email_pattern,
    }


def _normalize_domain(domain):
    if domain is None:
        return None
    normalized = str(domain).strip().lower()
    if normalized.startswith("@"):
        normalized = normalized[1:]
    return normalized or None


def _is_valid_domain(domain):
    # Conservative domain validation (no protocol/path, basic DNS label form)
    return bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+", domain or ""))


def _validate_pattern_template(pattern, required_placeholders=None):
    if not pattern:
        return False, "Pattern cannot be empty"

    placeholders = re.findall(r"\{(\w+)\}", pattern)
    if not placeholders:
        return False, "Pattern must include at least one placeholder like {enrollment}"

    if required_placeholders:
        missing = [p for p in required_placeholders if p not in placeholders]
        if missing:
            return False, f"Pattern must include placeholder(s): {', '.join(missing)}"

    if pattern.count('@') != 1:
        return False, "Pattern must contain exactly one '@'"

    try:
        regex_pattern = re.escape(pattern)
        for placeholder in placeholders:
            escaped_placeholder = re.escape(f"{{{placeholder}}}")
            regex_pattern = regex_pattern.replace(escaped_placeholder, r"([^@\-\.]+)")
        re.compile('^' + regex_pattern + '$', re.IGNORECASE)
    except re.error:
        return False, "Pattern could not be parsed"

    return True, None


def update_college_email_configuration(
    college_id,
    domain,
    student_email_pattern,
    personnel_email_pattern,
):
    """
    Update a college's domain and student/personnel email patterns.
    Intended for admin/HOD personnel setup after college registration.
    """
    college = get_college_by_id(college_id)
    if not college:
        return False, "College not found", None

    normalized_domain = _normalize_domain(domain)
    if not normalized_domain or not _is_valid_domain(normalized_domain):
        return False, "Invalid domain format", None

    student_pattern = (student_email_pattern or '').strip()
    personnel_pattern = (personnel_email_pattern or '').strip()

    ok, message = _validate_pattern_template(student_pattern)
    if not ok:
        return False, f"Invalid student email pattern: {message}", None

    ok, message = _validate_pattern_template(personnel_pattern, required_placeholders=['role'])
    if not ok:
        return False, f"Invalid personnel email pattern: {message}", None

    # Prevent domain collisions across colleges.
    existing = College.query.filter(College.domain == normalized_domain, College.id != college.id).first()
    if existing:
        return False, "Domain is already assigned to another college", None

    try:
        college.domain = normalized_domain
        college.student_email_pattern = student_pattern
        college.personnel_email_pattern = personnel_pattern
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return False, "Could not update college email configuration", None

    return True, None, {
        "college_id": college.id,
        "domain": college.domain,
        "student_email_pattern": college.student_email_pattern,
        "personnel_email_pattern": college.personnel_email_pattern,
    }
