"""
College Personnel Model

Database schema for college staff, faculty, HODs, etc.
"""

from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class CollegePersonnel(db.Model):
    """
    College personnel model for staff, faculty, HODs, admins.
    
    Roles:
    - admin: Full access to college management
    - hod: Department head, can manage students and some personnel
    - faculty: Teaching staff, limited access
    - staff: Administrative staff, limited access
    - assistant: Support staff, minimal access
    - coordinator: Event/program coordinators, moderate access
    """
    __tablename__ = "college_personnel"

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=False)
    
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    role = db.Column(db.String(50), nullable=False)
    personnel_id = db.Column(db.String(50), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    can_manage_students = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_personnel = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    college = db.relationship("College", backref="personnel")
    
    # Database constraints
    __table_args__ = (
        db.CheckConstraint(
            role.in_(['admin', 'hod', 'faculty', 'staff', 'assistant', 'coordinator']),
            name='valid_role'
        ),
    )
    
    # ===== AUTHENTICATION METHODS =====
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    # ===== UTILITY METHODS =====
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_role_display(self):
        """Return capitalized role name"""
        return self.role.upper() if self.role in ['hod'] else self.role.capitalize()
    
    def has_permission(self, permission):
        """Check if personnel has specific permission"""
        if permission == 'manage_students':
            return self.can_manage_students
        elif permission == 'manage_personnel':
            return self.can_manage_personnel
        return False
    
    def set_role_permissions(self):
        """Set default permissions based on role"""
        if self.role in ['admin', 'hod']:
            self.can_manage_students = True
            self.can_manage_personnel = True
        elif self.role == 'coordinator':
            self.can_manage_students = True
            self.can_manage_personnel = False
        else:  # faculty, staff, assistant
            self.can_manage_students = False
            self.can_manage_personnel = False
    
    def get_profile_summary(self):
        """Return profile data for display"""
        return {
            'personnel_id': self.id,
            'full_name': self.get_full_name(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'role': self.role,
            'role_display': self.get_role_display(),
            'personnel_id_number': self.personnel_id,
            'college_id': self.college_id,
            'college_name': self.college.name if self.college else None,
            'is_active': self.is_active,
            'can_manage_students': self.can_manage_students,
            'can_manage_personnel': self.can_manage_personnel,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<CollegePersonnel {self.get_full_name()} ({self.role}) at {self.college.name if self.college else 'Unknown'}>"
