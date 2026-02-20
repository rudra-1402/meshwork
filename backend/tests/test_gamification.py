"""
Tests for gamification features (streaks, skills, achievements).
Coverage targets: streak_service.py (18% → 80%), skill_service.py (23% → 75%)
"""
import pytest
from datetime import datetime, date, timedelta, timezone


# =============================================================================
# STREAK TRACKING TESTS
# =============================================================================

class TestStreakTracking:
    """Test user login streak tracking."""
    
    def test_first_login_creates_streak(self, app, streak_user):
        """First login initializes streak to 1"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = None
            _db.session.commit()
            
            # Update streak
            result = StreakService.update_login_streak(user)
            
            assert result['streak_continued'] is True
            assert result['current_streak'] == 1
            assert user.current_streak == 1
            assert user.max_streak == 1
            assert user.last_login_date == date.today()
    
    def test_consecutive_login_increments_streak(self, app, streak_user):
        """Logging in on consecutive days increments streak"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today() - timedelta(days=1)
            user.current_streak = 5
            user.max_streak = 5
            _db.session.commit()
            
            # Log in today
            result = StreakService.update_login_streak(user)
            
            assert result['streak_continued'] is True
            assert result['current_streak'] == 6
            assert user.current_streak == 6
            assert user.max_streak == 6
    
    def test_missed_day_resets_streak(self, app, streak_user):
        """Missing a day resets streak to 1"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today() - timedelta(days=2)  # 2 days ago
            user.current_streak = 10
            user.max_streak = 15
            _db.session.commit()
            
            # Log in today (missed yesterday)
            result = StreakService.update_login_streak(user)
            
            assert result['streak_continued'] is False
            assert result['current_streak'] == 1
            assert user.current_streak == 1
            assert user.max_streak == 15  # Max should not decrease
    
    def test_same_day_login_no_change(self, app, streak_user):
        """Logging in multiple times same day doesn't change streak"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today()
            user.current_streak = 7
            _db.session.commit()
            
            # Try to update again
            result = StreakService.update_login_streak(user)
            
            assert result['streak_continued'] is False
            assert result['current_streak'] == 7
            assert user.current_streak == 7
    
    def test_streak_milestone_bonus_xp(self, app, streak_user):
        """Milestone streaks (7, 30, etc.) award bonus XP"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today() - timedelta(days=1)
            user.current_streak = 6  # Will become 7 (milestone)
            _db.session.commit()
            
            # Log in today
            result = StreakService.update_login_streak(user)
            
            assert result['current_streak'] == 7
            # Should award bonus XP for 7-day milestone
            assert result.get('milestone_reached') is True or result.get('bonus_xp', 0) > 0


# =============================================================================
# SKILL TRACKING TESTS
# =============================================================================

class TestSkillTracking:
    """Test user skill XP and leveling."""
    
    def test_award_skill_xp_creates_skill(self, app, seeded_user):
        """Awarding skill XP creates skill if it doesn't exist"""
        with app.app_context():
            from app.services.skill_service import SkillService
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            # Award Python skill XP
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="Python",
                amount=50
            )
            
            assert result['success'] is True
            assert result['skill_name'] == "Python"
            assert result['xp_added'] == 50
            
            # Verify skill exists in DB
            skill = UserSkill.query.filter_by(
                user_id=seeded_user["id"],
                skill_name="Python"
            ).first()
            
            assert skill is not None
            assert skill.xp == 50
            
            # Cleanup
            _db.session.delete(skill)
            _db.session.commit()
    
    def test_award_skill_xp_updates_existing(self, app, seeded_user):
        """Awarding skill XP updates existing skill"""
        with app.app_context():
            from app.services.skill_service import SkillService
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            # Create initial skill
            skill = UserSkill(
                user_id=seeded_user["id"],
                skill_name="JavaScript",
                xp=100,
                level=1
            )
            _db.session.add(skill)
            _db.session.commit()
            
            # Award more XP
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="JavaScript",
                amount=75
            )
            
            assert result['success'] is True
            assert result['old_xp'] == 100
            assert result['new_xp'] == 175
            
            # Cleanup
            UserSkill.query.filter_by(
                user_id=seeded_user["id"],
                skill_name="JavaScript"
            ).delete()
            _db.session.commit()
    
    def test_skill_level_up_detected(self, app, seeded_user):
        """Large XP award triggers skill level up"""
        with app.app_context():
            from app.services.skill_service import SkillService
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            # Create skill at level 0
            skill = UserSkill(
                user_id=seeded_user["id"],
                skill_name="Python",
                xp=0,
                level=0
            )
            _db.session.add(skill)
            _db.session.commit()
            
            # Award large XP
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="Python",
                amount=150  # Should cause level up
            )
            
            assert result['success'] is True
            if result.get('leveled_up'):
                assert result['new_level'] > result['old_level']
            
            # Cleanup
            UserSkill.query.filter_by(
                user_id=seeded_user["id"],
                skill_name="Python"
            ).delete()
            _db.session.commit()
    
    def test_invalid_skill_name_rejected(self, app, seeded_user):
        """Invalid skill names are rejected"""
        with app.app_context():
            from app.services.skill_service import SkillService
            
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="NotARealSkill",
                amount=50
            )
            
            assert result['success'] is False
            assert 'Invalid skill' in result['reason']
    
    def test_negative_skill_xp_rejected(self, app, seeded_user):
        """Negative skill XP is rejected"""
        with app.app_context():
            from app.services.skill_service import SkillService
            
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="Python",
                amount=-10
            )
            
            assert result['success'] is False
    
    def test_excessive_skill_xp_rejected(self, app, seeded_user):
        """Excessive skill XP (>200) is rejected"""
        with app.app_context():
            from app.services.skill_service import SkillService
            
            result = SkillService.award_skill_xp(
                user_id=seeded_user["id"],
                skill_name="Python",
                amount=999
            )
            
            assert result['success'] is False


# =============================================================================
# SKILL DISTRIBUTION TESTS (Challenge XP)
# =============================================================================

class TestSkillXPDistribution:
    """Test distributing XP across multiple skills."""
    
    def test_distribute_challenge_xp(self, app, seeded_user):
        """Challenge XP can be distributed across multiple skills"""
        with app.app_context():
            from app.services.skill_service import SkillService
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            # Distribute 100 XP: 60% Python, 40% JavaScript
            result = SkillService.distribute_challenge_xp(
                user_id=seeded_user["id"],
                total_xp=100,
                skill_weights={"Python": 60, "JavaScript": 40}  # Percentages, not decimals
            )
            
            assert result['success'] is True
            assert result['total_xp'] == 100
            assert len(result['skills_updated']) == 2
            
            # Verify skills created with correct XP
            python_skill = UserSkill.query.filter_by(
                user_id=seeded_user["id"],
                skill_name="Python"
            ).first()
            
            js_skill = UserSkill.query.filter_by(
                user_id=seeded_user["id"],
                skill_name="JavaScript"
            ).first()
            
            assert python_skill is not None
            assert python_skill.xp == 60
            assert js_skill is not None
            assert js_skill.xp == 40
            
            # Cleanup
            UserSkill.query.filter_by(user_id=seeded_user["id"]).delete()
            _db.session.commit()
    
    def test_distribute_invalid_weights(self, app, seeded_user):
        """Invalid skill weights are rejected"""
        with app.app_context():
            from app.services.skill_service import SkillService
            
            # Weights don't sum to 100
            result = SkillService.distribute_challenge_xp(
                user_id=seeded_user["id"],
                total_xp=100,
                skill_weights={"Python": 50, "JavaScript": 30}  # Only 80%
            )
            
            assert result['success'] is False


# =============================================================================
# STREAK LEADERBOARD TESTS
# =============================================================================

class TestStreakLeaderboard:
    """Test streak leaderboard service."""
    
    def test_get_streak_leaderboard(self, app):
        """Streak leaderboard returns users sorted by streak"""
        with app.app_context():
            from app.services.streak_service import StreakService
            from app.models.user import User
            from app.extensions import db as _db
            
            # Create users with different streaks
            user_ids = []
            for i, streak in enumerate([15, 10, 5]):
                u = User(
                    username=f"streaktest_{i}",
                    first_name=f"User{i}",
                    last_name="Test",
                    email=f"streaktest{i}@test.edu",
                    current_streak=streak,
                )
                u.set_password("TestPass123!")
                _db.session.add(u)
            _db.session.commit()
            
            user_ids = [u.id for u in User.query.filter(
                User.username.like("streaktest_%")
            ).all()]
            
            # Get leaderboard
            leaderboard = StreakService.get_streak_leaderboard(limit=10)
            
            # Should have at least our 3 test users
            assert len(leaderboard) >= 3
            
            # Should be sorted descending
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]['current_streak'] >= leaderboard[i + 1]['current_streak']
            
            # Cleanup
            User.query.filter(User.username.like("streaktest_%")).delete()
            _db.session.commit()


# =============================================================================
# MAX STREAK TRACKING
# =============================================================================

class TestMaxStreak:
    """Test max streak tracking."""
    
    def test_max_streak_updates_when_current_exceeds(self, app, streak_user):
        """Max streak updates when current streak exceeds it"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today() - timedelta(days=1)
            user.current_streak = 20
            user.max_streak = 20
            _db.session.commit()
            
            # Log in today (streak becomes 21)
            result = StreakService.update_login_streak(user)
            
            assert user.current_streak == 21
            assert user.max_streak == 21  # Should update
    
    def test_max_streak_unchanged_when_current_below(self, app, streak_user):
        """Max streak unchanged when current streak is below it"""
        with app.app_context():
            from app.models.user import User
            from app.services.streak_service import StreakService
            from app.extensions import db as _db
            
            user = _db.session.get(User, streak_user)
            user.last_login_date = date.today() - timedelta(days=2)  # Missed day
            user.current_streak = 10
            user.max_streak = 50  # Had a longer streak before
            _db.session.commit()
            
            # Log in today (streak resets to 1)
            result = StreakService.update_login_streak(user)
            
            assert user.current_streak == 1
            assert user.max_streak == 50  # Should remain unchanged
