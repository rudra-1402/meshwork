"""
UserSkill Model

Tracks user proficiency in specific technologies/skills.
Each skill has its own XP and level calculated separately from account XP.

Business logic has been moved to services/skill_service.py
"""

from app.extensions import db
from datetime import datetime
import math


class UserSkill(db.Model):
    """
    User skill proficiency tracking.
    
    Each user can have multiple skills (Python, JavaScript, React, etc.)
    Each skill has separate XP and level progression.
    
    Business Logic Location:
    - Skill XP awarding → services/skill_service.py
    - Challenge XP distribution → services/skill_service.py
    - Skill weight validation → services/skill_service.py
    """
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Skill name (e.g., "Python", "JavaScript", "React")
    skill_name = db.Column(db.String(100), nullable=False)
    
    # Skill-specific XP
    xp = db.Column(db.Integer, default=0, nullable=False)
    
    # Skill level (calculated from XP)
    level = db.Column(db.Integer, default=0, nullable=False)
    
    # Last activity with this skill
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ===== RELATIONSHIPS =====
    user = db.relationship("User", backref="skills")
    
    # ===== CONSTRAINTS & INDEXES =====
    __table_args__ = (
        # One skill record per user per skill
        db.UniqueConstraint('user_id', 'skill_name', name='uix_user_skill'),
        # Index for efficient lookups
        db.Index('idx_user_skills', 'user_id', 'skill_name'),
    )
    
    # ===== LEVEL CALCULATION (Pure Functions - OK in Model) =====
    
    @staticmethod
    def calculate_level_from_xp(xp):
        """
        Calculate skill level from XP using standardized formula.
        
        Formula: level = floor(sqrt(xp / 100))
        
        This matches the User model formula for consistency.
        
        This is a PURE FUNCTION - no database access, no side effects.
        
        Examples:
            0-99 XP → Level 0
            100-399 XP → Level 1
            400-899 XP → Level 2
            900-1599 XP → Level 3
            2500 XP → Level 5
            10,000 XP → Level 10
        
        Args:
            xp: Total XP for the skill
            
        Returns:
            Integer level (minimum 0)
        """
        if xp < 0:
            return 0
        
        # Use same formula as User level for consistency
        # level = sqrt(xp / 100)
        level = int(math.sqrt(xp / 100))
        
        return max(0, level)
    
    def update_level(self):
        """
        Update skill level based on current XP.
        
        This is a SIMPLE FIELD UPDATE - allowed in model.
        
        Returns:
            tuple: (leveled_up: bool, old_level: int, new_level: int)
        """
        old_level = self.level
        self.level = self.calculate_level_from_xp(self.xp)
        
        leveled_up = self.level > old_level
        
        return leveled_up, old_level, self.level
    
    # ===== READ-ONLY QUERIES (OK in Model) =====
    
    @staticmethod
    def get_user_top_skills(user_id, limit=5):
        """
        Get user's top skills by XP.
        
        This is a READ-ONLY QUERY - allowed in model.
        
        Args:
            user_id: User ID
            limit: Number of skills to return
            
        Returns:
            List of UserSkill instances
        """
        return (
            UserSkill.query
            .filter_by(user_id=user_id)
            .order_by(UserSkill.xp.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_user_skills_summary(user_id):
        """
        Get summary of all user skills for profile display.
        
        This is a READ-ONLY aggregation - allowed in model.
        
        Args:
            user_id: User ID
            
        Returns:
            dict: {
                'total_skills': int,
                'total_skill_xp': int,
                'top_skills': list,
                'level_breakdown': dict
            }
        """
        all_skills = UserSkill.query.filter_by(user_id=user_id).all()
        
        total_xp = sum(s.xp for s in all_skills)
        
        # Top 5 skills by XP
        top_skills = sorted(all_skills, key=lambda s: s.xp, reverse=True)[:5]
        
        # Breakdown by level
        level_breakdown = {}
        for skill in all_skills:
            level_key = f"Level {skill.level}"
            level_breakdown[level_key] = level_breakdown.get(level_key, 0) + 1
        
        return {
            'total_skills': len(all_skills),
            'total_skill_xp': total_xp,
            'top_skills': [
                {
                    'skill_name': s.skill_name,
                    'level': s.level,
                    'xp': s.xp,
                    'last_activity': s.last_activity_at.isoformat() if s.last_activity_at else None
                }
                for s in top_skills
            ],
            'level_breakdown': level_breakdown
        }
    
    def __repr__(self):
        return f"<UserSkill user={self.user_id} {self.skill_name} L{self.level} ({self.xp} XP)>"