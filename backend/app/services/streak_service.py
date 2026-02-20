"""
Streak Service

Manages user login streaks, streak bonuses, and streak-based milestones.
"""

from app.extensions import db
from app.constants.gamification import STREAK_BONUS_XP
from datetime import date, timedelta


class StreakService:
    """
    Centralized streak management service.
    
    Handles:
    - Login streak tracking
    - Streak bonus XP calculation
    - Streak milestone detection
    """
    
    @staticmethod
    def update_login_streak(user):
        """
        Update user's login streak based on last login date.
        
        This should be called on EVERY successful login.
        
        Args:
            user: User instance (will be modified)
            
        Returns:
            dict: {
                'streak_continued': bool,
                'current_streak': int,
                'old_streak': int (if broken),
                'bonus_xp': int,
                'message': str,
                'milestone_reached': bool
            }
        """
        today = date.today()
        
        # Case 1: First login ever
        if user.last_login_date is None:
            user.current_streak = 1
            user.max_streak = 1
            user.last_login_date = today
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            return {
                'streak_continued': True,
                'first_login_today': True,
                'current_streak': 1,
                'bonus_xp': 0,
                'message': 'Welcome! Your streak has started!',
                'milestone_reached': False
            }

        # Case 2: Already logged in today
        if user.last_login_date == today:
            return {
                'streak_continued': False,
                'first_login_today': False,
                'current_streak': user.current_streak,
                'bonus_xp': 0,
                'message': 'Already logged in today',
                'milestone_reached': False
            }

        # Case 3: Check if streak continues (logged in yesterday)
        yesterday = today - timedelta(days=1)

        if user.last_login_date == yesterday:
            # Streak continues!
            old_streak = user.current_streak
            user.current_streak += 1
            user.last_login_date = today

            # Update max streak
            if user.current_streak > user.max_streak:
                user.max_streak = user.current_streak

            # Check for milestone bonus
            bonus_xp = STREAK_BONUS_XP.get(user.current_streak, 0)
            milestone_reached = bonus_xp > 0

            # Award milestone XP inside the same logical unit — XPService.award_xp
            # commits internally; if it fails it rolls back its own transaction and
            # re-raises, which we catch here to roll back the streak changes too.
            try:
                db.session.flush()  # Stage streak fields without committing yet
                if bonus_xp > 0:
                    from app.services.xp_service import XPService
                    xp_result = XPService.award_xp(
                        user=user,
                        amount=bonus_xp,
                        source=f'streak_bonus_{user.current_streak}',
                        description=f'{user.current_streak} day streak milestone bonus!',
                        bypass_cap=True  # Streak bonuses bypass daily cap
                    )
                    if not xp_result['success']:
                        bonus_xp = 0
                else:
                    db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            message = f'{user.current_streak} day streak!'
            if milestone_reached:
                message += f' Milestone bonus: +{bonus_xp} XP!'

            return {
                'streak_continued': True,
                'first_login_today': True,
                'current_streak': user.current_streak,
                'old_streak': old_streak,
                'bonus_xp': bonus_xp,
                'message': message,
                'milestone_reached': milestone_reached
            }

        # Case 4: Streak broken
        else:
            old_streak = user.current_streak
            user.current_streak = 1
            user.last_login_date = today

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            return {
                'streak_continued': False,
                'first_login_today': True,
                'current_streak': 1,
                'old_streak': old_streak,
                'bonus_xp': 0,
                'message': f'Streak broken! (Was {old_streak} days). New streak started.',
                'milestone_reached': False
            }
    
    @staticmethod
    def get_streak_status(user):
        """
        Get current streak status without updating it.
        
        Args:
            user: User instance
            
        Returns:
            dict: {
                'current_streak': int,
                'max_streak': int,
                'last_login_date': str,
                'next_milestone': int or None,
                'next_milestone_bonus': int or None,
                'days_until_next_milestone': int or None
            }
        """
        current_streak = user.current_streak
        
        # Find next milestone
        next_milestone = None
        next_milestone_bonus = None
        
        milestones = sorted(STREAK_BONUS_XP.keys())
        for milestone in milestones:
            if milestone > current_streak:
                next_milestone = milestone
                next_milestone_bonus = STREAK_BONUS_XP[milestone]
                break
        
        days_until_next = None
        if next_milestone:
            days_until_next = next_milestone - current_streak
        
        return {
            'current_streak': current_streak,
            'max_streak': user.max_streak,
            'last_login_date': user.last_login_date.isoformat() if user.last_login_date else None,
            'next_milestone': next_milestone,
            'next_milestone_bonus': next_milestone_bonus,
            'days_until_next_milestone': days_until_next
        }
    
    @staticmethod
    def get_all_milestones():
        """
        Get all streak milestones and their bonuses.
        
        Returns:
            list: [
                {'days': 7, 'bonus_xp': 25, 'name': '1 Week'},
                {'days': 30, 'bonus_xp': 150, 'name': '1 Month'},
                ...
            ]
        """
        milestone_names = {
            7: '1 Week',
            30: '1 Month',
            90: '3 Months',
            150: '5 Months',
            365: '1 Year',
        }
        
        milestones = []
        for days in sorted(STREAK_BONUS_XP.keys()):
            milestones.append({
                'days': days,
                'bonus_xp': STREAK_BONUS_XP[days],
                'name': milestone_names.get(days, f'{days} Days')
            })
        
        return milestones
    
    @staticmethod
    def get_streak_leaderboard(limit=10):
        """
        Get users with longest current streaks.
        
        Args:
            limit: Number of users to return
            
        Returns:
            list: Top users by current streak
        """
        from app.models.user import User
        
        top_users = (
            User.query
            .filter(User.current_streak > 0)
            .order_by(User.current_streak.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                'user_id': u.id,
                'username': u.username,
                'current_streak': u.current_streak,
                'max_streak': u.max_streak,
                'last_login_date': u.last_login_date.isoformat() if u.last_login_date else None
            }
            for u in top_users
        ]
    
    @staticmethod
    def check_streak_at_risk(user):
        """
        Check if user's streak is at risk of breaking.
        
        A streak is at risk if user hasn't logged in today yet.
        
        Args:
            user: User instance
            
        Returns:
            dict: {
                'at_risk': bool,
                'last_login': str,
                'hours_remaining': int (approximate)
            }
        """
        today = date.today()
        
        if user.last_login_date is None:
            return {
                'at_risk': False,
                'last_login': None,
                'hours_remaining': None
            }
        
        # If logged in today, not at risk
        if user.last_login_date == today:
            return {
                'at_risk': False,
                'last_login': user.last_login_date.isoformat(),
                'hours_remaining': None
            }
        
        # If logged in yesterday, at risk (need to login today)
        yesterday = today - timedelta(days=1)
        if user.last_login_date == yesterday:
            # Rough estimate: assume 12 hours remaining in day
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            hours_until_midnight = 24 - now.hour
            
            return {
                'at_risk': True,
                'last_login': user.last_login_date.isoformat(),
                'hours_remaining': hours_until_midnight,
                'message': f'Login today to keep your {user.current_streak} day streak!'
            }
        
        # If last login was before yesterday, streak already broken
        return {
            'at_risk': False,
            'last_login': user.last_login_date.isoformat(),
            'hours_remaining': None,
            'message': 'Streak has already been broken. Login to start a new one!'
        }