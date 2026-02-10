from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class College(db.Model):
    __tablename__ = "colleges"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    domain = db.Column(db.String(255), nullable=True)
    student_email_pattern = db.Column(db.String(500), nullable=True)
    personnel_email_pattern = db.Column(db.String(500), nullable=True)
    registration_number = db.Column(db.String(100), unique=True, nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    users = db.relationship(
        "User",
        back_populates="college",
        cascade="all, delete-orphan"
    )
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_address(self):
        """Return formatted address"""
        parts = [self.name]
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        return ", ".join(parts)
    
    def validate_student_email(self, email):
        """Check if email matches student pattern"""
        # Will be implemented in EmailValidationService
        pass
    
    def validate_personnel_email(self, email):
        """Check if email matches personnel pattern"""
        # Will be implemented in EmailValidationService
        pass
