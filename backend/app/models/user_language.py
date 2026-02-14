from app.extensions import db
from datetime import datetime, timezone


class UserLanguage(db.Model):
    """
    Tracks user proficiency in programming languages.
    Each language has its own level and XP, calculated from project contributions.
    Used for community leadership gatekeeping (e.g., Java community requires Java expertise).
    """
    __tablename__ = "user_languages"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Programming language name (e.g., "Python", "Java", "JavaScript")
    language = db.Column(db.String(50), nullable=False)
    
    # Language-specific level (1-100, calculated from language_xp)
    # Used for gatekeeping: "Create Java community requires Java level >= 25"
    language_level = db.Column(db.Integer, default=1, nullable=False)
    
    # Language-specific XP
    # Gained from: project creation, commits, event participation using this language
    language_xp = db.Column(db.Integer, default=0, nullable=False)
    
    # Last activity timestamp (for "recently active in Python" queries)
    last_activity_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationship to User model
    user = db.relationship("User", backref=db.backref("languages", lazy="dynamic"))
    
    # Composite unique constraint: one record per user-language pair
    __table_args__ = (
        db.UniqueConstraint('user_id', 'language', name='uix_user_language'),
    )
    
    def __repr__(self):
        return f"<UserLanguage user_id={self.user_id} language={self.language} level={self.language_level}>"
    
    @staticmethod
    def calculate_level_from_xp(xp):
        """
        Calculate language level from XP using a progressive curve.
        
        Level progression (example curve - adjust as needed):
        - Level 1: 0-99 XP
        - Level 2: 100-249 XP
        - Level 3: 250-499 XP
        - Level 10: ~5000 XP
        - Level 25: ~30,000 XP (community leadership threshold)
        - Level 50: ~150,000 XP (expert)
        - Level 100: ~1,000,000 XP (mastery)
        
        Formula: level = floor(sqrt(xp / 50)) + 1
        This creates a smooth curve where early levels are fast, later levels slower.
        
        Args:
            xp: Total XP for the language
            
        Returns:
            Integer level (1-100)
        """
        import math
        
        if xp < 0:
            return 1
        
        # Square root progression for smooth leveling
        level = int(math.sqrt(xp / 50)) + 1
        
        # Cap at level 100
        return min(level, 100)
    
    def add_xp(self, xp_gain):
        """
        Add XP to this language and recalculate level.
        
        Args:
            xp_gain: Amount of XP to add (integer)
            
        Returns:
            Dict with old_level, new_level, xp_gained, leveled_up (bool)
        """
        old_level = self.language_level
        old_xp = self.language_xp
        
        self.language_xp += xp_gain
        self.language_level = self.calculate_level_from_xp(self.language_xp)
        self.last_activity_at = datetime.now(timezone.utc)
        
        leveled_up = self.language_level > old_level
        
        return {
            "language": self.language,
            "old_level": old_level,
            "new_level": self.language_level,
            "old_xp": old_xp,
            "new_xp": self.language_xp,
            "xp_gained": xp_gain,
            "leveled_up": leveled_up
        }
