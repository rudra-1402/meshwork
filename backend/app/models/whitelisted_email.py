"""
Whitelisted Email Model

Database schema for pre-registered student emails.
HODs/Admins can whitelist emails before students sign up.
"""

from app.extensions import db
from datetime import datetime


class WhitelistedEmail(db.Model):
    """
    Whitelisted email model for student pre-registration.
    
    HODs/Admins add student emails to this table.
    Students can only sign up if their email is whitelisted.
    """
    __tablename__ = "whitelisted_emails"

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=False)
    
    email = db.Column(db.String(255), unique=True, nullable=False)
    student_enrollment = db.Column(db.String(100), nullable=True)
    student_name = db.Column(db.String(255), nullable=True)
    
    added_by_personnel_id = db.Column(db.Integer, db.ForeignKey("college_personnel.id"), nullable=True)
    
    is_registered = db.Column(db.Boolean, default=False, nullable=False)
    registered_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    registration_date = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    college = db.relationship("College", backref="whitelisted_emails")
    added_by = db.relationship("CollegePersonnel", foreign_keys=[added_by_personnel_id])
    registered_user = db.relationship("User", foreign_keys=[registered_user_id])
    
    # ===== UTILITY METHODS =====
    
    def mark_as_registered(self, user_id):
        """Mark email as registered by user"""
        self.is_registered = True
        self.registered_user_id = user_id
        self.registration_date = datetime.utcnow()
    
    def get_status(self):
        """Return registration status"""
        if self.is_registered:
            return "Registered"
        return "Pending"
    
    def to_dict(self):
        """Return dictionary representation"""
        return {
            'id': self.id,
            'email': self.email,
            'student_enrollment': self.student_enrollment,
            'student_name': self.student_name,
            'is_registered': self.is_registered,
            'status': self.get_status(),
            'added_by': self.added_by.get_full_name() if self.added_by else 'System',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        status = "Registered" if self.is_registered else "Pending"
        return f"<WhitelistedEmail {self.email} ({status})>"
