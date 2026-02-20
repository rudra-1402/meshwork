"""
Tests for the XP/scoring system.

Split into two layers:
  1. Pure unit tests — User model methods, no DB needed
  2. Service integration tests — XPService.award_xp, requires a real DB user (xp_user fixture)
"""
import pytest


# =============================================================================
# PURE UNIT TESTS — User.calculate_level_from_xp
# No database, no fixtures.
# =============================================================================

class TestLevelCalculation:
    """User.calculate_level_from_xp is a pure static method — test it in isolation."""

    def test_zero_xp_is_level_1(self):
        from app.models.user import User
        assert User.calculate_level_from_xp(0) == 1

    def test_negative_xp_is_level_1(self):
        from app.models.user import User
        assert User.calculate_level_from_xp(-500) == 1

    def test_level_thresholds(self):
        from app.models.user import User
        # Formula: floor(sqrt(xp / 100)) + 1
        cases = [
            (0,     1),
            (99,    1),
            (100,   2),
            (399,   2),
            (400,   3),
            (899,   3),
            (900,   4),
            (1600,  5),
            (10000, 11),
        ]
        for xp, expected_level in cases:
            assert User.calculate_level_from_xp(xp) == expected_level, (
                f"XP={xp} should be level {expected_level}"
            )

    def test_level_is_always_at_least_1(self):
        from app.models.user import User
        for xp in (0, 1, 50, 99):
            assert User.calculate_level_from_xp(xp) >= 1


class TestXPForNextLevel:
    """User.get_xp_for_next_level is a pure read-only calculation."""

    def test_returns_expected_keys(self, app):
        with app.app_context():
            from app.models.user import User
            u = User(username="tmp", first_name="T", last_name="U",
                     email="tmp@t.local", xp=0, level=1)
            info = u.get_xp_for_next_level()
            for key in ("current_level", "next_level", "current_xp",
                        "xp_needed_for_next", "progress_percentage"):
                assert key in info

    def test_progress_percentage_within_bounds(self, app):
        with app.app_context():
            from app.models.user import User
            for xp_val in (0, 50, 100, 500, 2500):
                u = User(username="tmp2", first_name="T", last_name="U",
                         email="tmp2@t.local",
                         xp=xp_val,
                         level=User.calculate_level_from_xp(xp_val))
                info = u.get_xp_for_next_level()
                assert 0 <= info["progress_percentage"] <= 100


# =============================================================================
# SERVICE INTEGRATION TESTS — XPService.award_xp
# These require a real user in the test DB (xp_user fixture).
# =============================================================================

class TestAwardXP:
    def test_award_positive_xp(self, app, xp_user):
        with app.app_context():
            from app.models.user import User
            from app.services.xp_service import XPService

            user = app.extensions["sqlalchemy"].session.get(User, xp_user)
            result = XPService.award_xp(user, 50, source="challenge", bypass_cap=True)

            assert result["success"] is True
            assert result["xp_awarded"] == 50

    def test_user_xp_increases_after_award(self, app, xp_user):
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService

            user = db.session.get(User, xp_user)
            xp_before = user.xp
            XPService.award_xp(user, 100, source="challenge", bypass_cap=True)

            # Re-fetch to confirm DB was updated
            db.session.expire(user)
            user = db.session.get(User, xp_user)
            assert user.xp == xp_before + 100

    def test_award_zero_xp_fails(self, app, xp_user):
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService

            user = db.session.get(User, xp_user)
            result = XPService.award_xp(user, 0, source="challenge")
            assert result["success"] is False

    def test_award_negative_xp_fails(self, app, xp_user):
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService

            user = db.session.get(User, xp_user)
            result = XPService.award_xp(user, -10, source="challenge")
            assert result["success"] is False

    def test_level_up_detected(self, app, xp_user):
        """Awarding enough XP to cross a level boundary sets leveled_up=True."""
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService

            user = db.session.get(User, xp_user)
            # Level 1 → Level 2 requires 100 XP
            result = XPService.award_xp(user, 100, source="challenge", bypass_cap=True)

            assert result["leveled_up"] is True
            assert result["new_level"] == 2
            assert result["old_level"] == 1

    def test_daily_cap_enforced(self, app, xp_user):
        """After hitting the 300 XP daily cap, further awards return 0."""
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService
            from app.constants.gamification import DAILY_XP_CAP

            user = db.session.get(User, xp_user)
            # Fill the daily cap exactly
            XPService.award_xp(user, DAILY_XP_CAP, source="challenge", bypass_cap=False)

            db.session.expire(user)
            user = db.session.get(User, xp_user)

            # Next award should be denied
            result = XPService.award_xp(user, 50, source="challenge", bypass_cap=False)
            assert result["success"] is False
            assert result["xp_awarded"] == 0

    def test_bypass_cap_ignores_daily_limit(self, app, xp_user):
        """bypass_cap=True awards XP even when daily cap is exceeded."""
        with app.app_context():
            from app.models.user import User
            from app.extensions import db
            from app.services.xp_service import XPService
            from app.constants.gamification import DAILY_XP_CAP

            user = db.session.get(User, xp_user)
            # Saturate the daily cap
            XPService.award_xp(user, DAILY_XP_CAP, source="challenge", bypass_cap=False)

            db.session.expire(user)
            user = db.session.get(User, xp_user)

            result = XPService.award_xp(user, 500, source="admin_bonus", bypass_cap=True)
            assert result["success"] is True
            assert result["xp_awarded"] == 500

    def test_xp_transaction_audit_created(self, app, xp_user):
        """Every successful award must create an XPTransaction audit record."""
        with app.app_context():
            from app.models.user import User
            from app.models.xp_transaction import XPTransaction
            from app.extensions import db
            from app.services.xp_service import XPService

            user = db.session.get(User, xp_user)
            before_count = XPTransaction.query.filter_by(user_id=xp_user).count()

            XPService.award_xp(user, 25, source="task", bypass_cap=True)

            after_count = XPTransaction.query.filter_by(user_id=xp_user).count()
            assert after_count == before_count + 1
