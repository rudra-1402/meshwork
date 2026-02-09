from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
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

    # Relationships
    college = db.relationship("College", back_populates="users")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # ===== GAMIFICATION METHODS =====
    
    @staticmethod
    def calculate_level_from_xp(xp):
        """
        Calculate level from XP using formula: XP = 100 × level²
        
        Level 1: 0-99 XP
        Level 2: 100-399 XP
        Level 3: 400-899 XP
        Level 10: 10,000+ XP
        
        Args:
            xp: Total XP amount
            
        Returns:
            Integer level
        """
        import math
        
        if xp < 0:
            return 1
        
        # Solve for level: xp = 100 × level²
        # level = sqrt(xp / 100)
        level = int(math.sqrt(xp / 100)) + 1
        
        return max(1, level)
    
    def update_level(self):
        """Update user level based on current XP"""
        old_level = self.level
        self.level = self.calculate_level_from_xp(self.xp)
        
        # Check if leveled up
        if self.level > old_level:
            return True, old_level, self.level
        
        return False, old_level, self.level
    
    def get_xp_for_next_level(self):
        """
        Get XP needed for next level.
        
        Returns:
            Dict with current_level, next_level, current_xp, xp_needed
        """
        current_level = self.level
        next_level = current_level + 1
        
        # XP required for next level: 100 × next_level²
        xp_for_next = 100 * (next_level ** 2)
        
        # XP for current level start
        xp_for_current = 100 * (current_level ** 2)
        
        # Progress within current level
        xp_in_current_level = self.xp - xp_for_current
        xp_needed_for_next = xp_for_next - xp_for_current
        
        return {
            "current_level": current_level,
            "next_level": next_level,
            "current_xp": self.xp,
            "xp_in_current_level": xp_in_current_level,
            "xp_needed_for_next": xp_needed_for_next,
            "progress_percentage": (xp_in_current_level / xp_needed_for_next) * 100 if xp_needed_for_next > 0 else 100
        }
    
    def reset_daily_xp_if_needed(self):
        """Reset daily XP counter if it's a new day"""
        today = date.today()
        
        if self.last_xp_reset_date != today:
            self.daily_xp_earned = 0
            self.last_xp_reset_date = today
    
    def can_earn_xp(self, amount):
        """
        Check if user can earn XP (daily cap: 300 XP).
        
        Args:
            amount: XP amount to earn
            
        Returns:
            tuple: (can_earn: bool, actual_amount: int, reason: str)
        """
        self.reset_daily_xp_if_needed()
        
        DAILY_CAP = 300
        
        remaining = DAILY_CAP - self.daily_xp_earned
        
        if remaining <= 0:
            return False, 0, "Daily XP cap (300 XP) reached"
        
        if amount <= remaining:
            return True, amount, "Can earn full amount"
        
        # Partial XP
        return True, remaining, f"Can only earn {remaining} XP (daily cap)"
    
    def add_xp(self, amount, source, description=""):
        """
        Add XP to user account with daily cap check.
        
        Args:
            amount: XP to add
            source: String describing source ("login", "challenge", "project", etc.)
            description: Optional detailed description
            
        Returns:
            Dict with success, xp_awarded, leveled_up, new_level
        """
        can_earn, actual_amount, reason = self.can_earn_xp(amount)
        
        if not can_earn:
            return {
                "success": False,
                "xp_awarded": 0,
                "reason": reason,
                "leveled_up": False
            }
        
        # Add XP
        old_xp = self.xp
        self.xp += actual_amount
        self.daily_xp_earned += actual_amount
        
        # Update level
        leveled_up, old_level, new_level = self.update_level()
        
        # Log transaction (will be created separately)
        from app.models.xp_transaction import XPTransaction
        transaction = XPTransaction(
            user_id=self.id,
            amount=actual_amount,
            source=source,
            description=description,
            balance_before=old_xp,
            balance_after=self.xp
        )
        db.session.add(transaction)
        
        return {
            "success": True,
            "xp_awarded": actual_amount,
            "xp_requested": amount,
            "leveled_up": leveled_up,
            "old_level": old_level,
            "new_level": new_level,
            "reason": reason if actual_amount < amount else None
        }
    
    def update_streak(self):
        """
        Update login streak based on last login date.
        
        Returns:
            Dict with streak_continued, current_streak, bonus_xp
        """
        today = date.today()
        
        # First login ever
        if self.last_login_date is None:
            self.current_streak = 1
            self.last_login_date = today
            return {
                "streak_continued": True,
                "current_streak": 1,
                "bonus_xp": 0,
                "message": "Streak started!"
            }
        
        # Check if already logged in today
        if self.last_login_date == today:
            return {
                "streak_continued": False,
                "current_streak": self.current_streak,
                "bonus_xp": 0,
                "message": "Already logged in today"
            }
        
        # Check if streak continues (logged in yesterday)
        from datetime import timedelta
        yesterday = today - timedelta(days=1)
        
        if self.last_login_date == yesterday:
            # Streak continues!
            self.current_streak += 1
            self.last_login_date = today
            
            # Update max streak
            if self.current_streak > self.max_streak:
                self.max_streak = self.current_streak
            
            # Calculate bonus XP
            bonus_xp = 0
            if self.current_streak == 7:
                bonus_xp = 25
            elif self.current_streak == 30:
                bonus_xp = 150
            
            return {
                "streak_continued": True,
                "current_streak": self.current_streak,
                "bonus_xp": bonus_xp,
                "message": f"{self.current_streak} day streak!"
            }
        else:
            # Streak broken
            old_streak = self.current_streak
            self.current_streak = 1
            self.last_login_date = today
            
            return {
                "streak_continued": False,
                "current_streak": 1,
                "old_streak": old_streak,
                "bonus_xp": 0,
                "message": f"Streak broken! (Was {old_streak} days)"
            }
    
    def add_reputation(self, amount):
        """
        Add reputation points (from voting).
        
        Args:
            amount: +1 for upvote, -1 for downvote
        """
        self.reputation += amount
    
    def get_profile_summary(self):
        """
        Get summary for profile display.
        
        Returns:
            Dict with all profile stats
        """
        level_info = self.get_xp_for_next_level()
        
        return {
            "username": self.username,
            "level": self.level,
            "xp": self.xp,
            "xp_progress": level_info,
            "reputation": self.reputation,
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "daily_xp_earned": self.daily_xp_earned,
            "daily_xp_remaining": max(0, 300 - self.daily_xp_earned)
        }
