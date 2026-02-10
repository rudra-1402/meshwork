"""
College Personnel Services

Handles authentication and management of college personnel (HODs, faculty, staff, etc.)
"""

from app.extensions import db
from app.models.college_personnel import CollegePersonnel
from app.models.college import College
from datetime import datetime


def create_personnel(first_name, last_name, email, password, college_id, role, personnel_id=None):
    """
    Create college personnel account.
    
    Args:
        first_name (str): First name
        last_name (str): Last name
        email (str): Email address
        password (str): Plain text password (will be hashed)
        college_id (int): College ID
        role (str): Role (admin, hod, faculty, staff, assistant, coordinator)
        personnel_id (str, optional): Personnel ID number
        
    Returns:
        tuple: (success: bool, message: str, personnel: CollegePersonnel or None)
    """
    # Validate college exists
    college = College.query.get(college_id)
    if not college:
        return False, "College not found", None
    
    # Check if email already exists
    existing = CollegePersonnel.query.filter_by(email=email).first()
    if existing:
        return False, "Email already registered", None
    
    # Validate role
    valid_roles = ['admin', 'hod', 'faculty', 'staff', 'assistant', 'coordinator']
    if role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}", None
    
    try:
        # Create personnel
        personnel = CollegePersonnel(
            college_id=college_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            personnel_id=personnel_id
        )
        
        personnel.set_password(password)
        personnel.set_role_permissions()  # Set default permissions based on role
        
        db.session.add(personnel)
        db.session.commit()
        
        return True, "Personnel account created successfully", personnel
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating personnel: {str(e)}", None


def authenticate_personnel(email, password):
    """
    Authenticate personnel.
    
    Args:
        email (str): Email address
        password (str): Password
        
    Returns:
        CollegePersonnel or None: Personnel object if authenticated, None otherwise
    """
    personnel = CollegePersonnel.query.filter_by(email=email).first()
    
    if not personnel:
        return None
    
    if not personnel.is_active:
        return None
    
    if not personnel.check_password(password):
        return None
    
    return personnel


def get_personnel_by_email(email):
    """
    Fetch personnel by email.
    
    Args:
        email (str): Email address
        
    Returns:
        CollegePersonnel or None: Personnel object if found
    """
    return CollegePersonnel.query.filter_by(email=email).first()


def get_personnel_by_id(personnel_id):
    """
    Fetch personnel by ID.
    
    Args:
        personnel_id (int): Personnel ID
        
    Returns:
        CollegePersonnel or None: Personnel object if found
    """
    return CollegePersonnel.query.get(personnel_id)


def get_college_personnel(college_id, include_inactive=False):
    """
    Get all personnel for a college.
    
    Args:
        college_id (int): College ID
        include_inactive (bool): Include inactive personnel
        
    Returns:
        list: List of CollegePersonnel objects
    """
    query = CollegePersonnel.query.filter_by(college_id=college_id)
    
    if not include_inactive:
        query = query.filter_by(is_active=True)
    
    return query.order_by(CollegePersonnel.created_at.desc()).all()


def update_personnel_permissions(personnel_id, can_manage_students=None, can_manage_personnel=None):
    """
    Update personnel permissions.
    
    Args:
        personnel_id (int): Personnel ID
        can_manage_students (bool, optional): Permission to manage students
        can_manage_personnel (bool, optional): Permission to manage personnel
        
    Returns:
        tuple: (success: bool, message: str)
    """
    personnel = CollegePersonnel.query.get(personnel_id)
    
    if not personnel:
        return False, "Personnel not found"
    
    try:
        if can_manage_students is not None:
            personnel.can_manage_students = can_manage_students
        
        if can_manage_personnel is not None:
            personnel.can_manage_personnel = can_manage_personnel
        
        personnel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Permissions updated successfully"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating permissions: {str(e)}"


def update_personnel_info(personnel_id, first_name=None, last_name=None, 
                          personnel_id_number=None, role=None):
    """
    Update personnel information.
    
    Args:
        personnel_id (int): Personnel ID
        first_name (str, optional): New first name
        last_name (str, optional): New last name
        personnel_id_number (str, optional): New personnel ID number
        role (str, optional): New role
        
    Returns:
        tuple: (success: bool, message: str)
    """
    personnel = CollegePersonnel.query.get(personnel_id)
    
    if not personnel:
        return False, "Personnel not found"
    
    valid_roles = ['admin', 'hod', 'faculty', 'staff', 'assistant', 'coordinator']
    if role and role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    try:
        if first_name:
            personnel.first_name = first_name
        
        if last_name:
            personnel.last_name = last_name
        
        if personnel_id_number:
            personnel.personnel_id = personnel_id_number
        
        if role:
            personnel.role = role
            personnel.set_role_permissions()  # Update permissions based on new role
        
        personnel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Information updated successfully"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating information: {str(e)}"


def deactivate_personnel(personnel_id):
    """
    Deactivate personnel account.
    
    Args:
        personnel_id (int): Personnel ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    personnel = CollegePersonnel.query.get(personnel_id)
    
    if not personnel:
        return False, "Personnel not found"
    
    if not personnel.is_active:
        return False, "Personnel already inactive"
    
    try:
        personnel.is_active = False
        personnel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Personnel deactivated successfully"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error deactivating personnel: {str(e)}"


def activate_personnel(personnel_id):
    """
    Activate personnel account.
    
    Args:
        personnel_id (int): Personnel ID
        
    Returns:
        tuple: (success: bool, message: str)
    """
    personnel = CollegePersonnel.query.get(personnel_id)
    
    if not personnel:
        return False, "Personnel not found"
    
    if personnel.is_active:
        return False, "Personnel already active"
    
    try:
        personnel.is_active = True
        personnel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Personnel activated successfully"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error activating personnel: {str(e)}"


def change_personnel_password(personnel_id, old_password, new_password):
    """
    Change personnel password.
    
    Args:
        personnel_id (int): Personnel ID
        old_password (str): Current password
        new_password (str): New password
        
    Returns:
        tuple: (success: bool, message: str)
    """
    personnel = CollegePersonnel.query.get(personnel_id)
    
    if not personnel:
        return False, "Personnel not found"
    
    if not personnel.check_password(old_password):
        return False, "Current password is incorrect"
    
    try:
        personnel.set_password(new_password)
        personnel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Password changed successfully"
    
    except Exception as e:
        db.session.rollback()
        return False, f"Error changing password: {str(e)}"


def get_personnel_stats(college_id):
    """
    Get statistics about personnel.
    
    Args:
        college_id (int): College ID
        
    Returns:
        dict: Personnel statistics
    """
    total = CollegePersonnel.query.filter_by(college_id=college_id).count()
    active = CollegePersonnel.query.filter_by(
        college_id=college_id, is_active=True
    ).count()
    
    # Count by role
    role_counts = {}
    for role in ['admin', 'hod', 'faculty', 'staff', 'assistant', 'coordinator']:
        count = CollegePersonnel.query.filter_by(
            college_id=college_id, role=role, is_active=True
        ).count()
        role_counts[role] = count
    
    return {
        'total': total,
        'active': active,
        'inactive': total - active,
        'by_role': role_counts
    }
