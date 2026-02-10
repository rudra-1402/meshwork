"""
User Model (Gamified)

Database schema for users with gamification fields.
Business logic has been moved to services.
"""

from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import math


class User(db.Model):
    """
    User model with gamification features.
    
    Fields:
    - Basic auth: id, username, email, password_hash
    - Academic: college_id, has_completed_questionnaire
    - Gamification: xp, level, reputation, streaks, daily_xp tracking
    
    Business Logic Location:
    - XP awarding → services/xp_service.py
    - Streak tracking → services/streak_service.py
    - Reputation → services/reputation_service.py (future)
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    college_id = db.Column(
        db.Integer,
        db.ForeignKey("colleges.id"),
        nullable=True
    )

    has_completed_questionnaire = db.Column(db.Boolean, default=False, nullable=False)

    # ===== GAMIFICATION FIELDS =====
    
    # Account XP & Level
    xp = db.Column(db.Integer, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    
    # Reputation (from voting)
    reputation = db.Column(db.Integer, default=0, nullable=False)
    
    # Streak tracking
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    max_streak = db.Column(db.Integer, default=0, nullable=False)
    last_login_date = db.Column(db.Date, nullable=True)
    
    # Daily XP cap tracking (resets daily)
    daily_xp_earned = db.Column(db.Integer, default=0, nullable=False)
    last_xp_reset_date = db.Column(db.Date, nullable=True)

    # ===== RELATIONSHIPS =====
    college = db.relationship("College", back_populates="users")

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ===== AUTHENTICATION METHODS =====
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def update_username(self, new_username):
        """
        Update username with availability check.
        Returns (success: bool, message: str)
        """
        if User.query.filter_by(username=new_username).first():
            return False, "Username already taken"
        self.username = new_username
        return True, "Username updated successfully"
    
    # ===== LEVEL CALCULATION (Pure Functions - OK in Model) =====
    
    @staticmethod
    def calculate_level_from_xp(xp):
        """
        Calculate level from XP using standardized formula.
        
        Formula: level = floor(sqrt(xp / 100)) + 1
        
        This is a PURE FUNCTION - no database access, no side effects.
        
        Examples:
            0 XP → Level 1
            100 XP → Level 2
            400 XP → Level 3
            900 XP → Level 4
            10,000 XP → Level 11
        
        Args:
            xp: Total XP amount
            
        Returns:
            Integer level (minimum 1)
        """
        if xp < 0:
            return 1
        
        # Standard formula: level = sqrt(xp / 100) + 1
        level = int(math.sqrt(xp / 100)) + 1
        
        return max(1, level)
    
    def update_level(self):
        """
        Update user level based on current XP.
        
        This is a SIMPLE FIELD UPDATE - allowed in model.
        No complex business logic, no external dependencies.
        
        Returns:
            tuple: (leveled_up: bool, old_level: int, new_level: int)
        """
        old_level = self.level
        self.level = self.calculate_level_from_xp(self.xp)
        
        leveled_up = self.level > old_level
        
        return leveled_up, old_level, self.level
    
    def get_xp_for_next_level(self):
        """
        Calculate XP needed for next level.
        
        This is a READ-ONLY CALCULATION - allowed in model.
        
        Returns:
            dict: {
                'current_level': int,
                'next_level': int,
                'current_xp': int,
                'xp_in_current_level': int,
                'xp_needed_for_next': int,
                'progress_percentage': float
            }
        """
        current_level = self.level
        next_level = current_level + 1
        
        # XP required for next level: 100 × (next_level - 1)²
        xp_for_next = 100 * ((next_level - 1) ** 2)
        
        # XP for current level start: 100 × (current_level - 1)²
        xp_for_current = 100 * ((current_level - 1) ** 2)
        
        # Progress within current level
        xp_in_current_level = self.xp - xp_for_current
        xp_needed_for_next = xp_for_next - xp_for_current
        
        # Calculate percentage
        if xp_needed_for_next > 0:
            progress_percentage = (xp_in_current_level / xp_needed_for_next) * 100
        else:
            progress_percentage = 100
        
        return {
            'current_level': current_level,
            'next_level': next_level,
            'current_xp': self.xp,
            'xp_in_current_level': xp_in_current_level,
            'xp_needed_for_next': xp_needed_for_next,
            'progress_percentage': min(100, max(0, progress_percentage))
        }
    
    # ===== PROFILE DISPLAY (Read-Only - OK in Model) =====
    
    def get_profile_summary(self):
        """
        Get summary for profile display.
        
        This is a READ-ONLY aggregation - allowed in model.
        
        Returns:
            dict: All profile stats for display
        """
        level_info = self.get_xp_for_next_level()
        
        return {
            'user_id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'level': self.level,
            'xp': self.xp,
            'xp_progress': level_info,
            'reputation': self.reputation,
            'current_streak': self.current_streak,
            'max_streak': self.max_streak,
            'daily_xp_earned': self.daily_xp_earned,
            'daily_xp_remaining': max(0, 300 - self.daily_xp_earned),  # 300 = DAILY_XP_CAP
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<User {self.username} (L{self.level}, {self.xp} XP)>"