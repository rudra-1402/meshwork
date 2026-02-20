from app.extensions import db
from datetime import datetime, timezone
import math


class UserLanguage(db.Model):
    """
    Tracks a user's relationship with a programming language.

    Two distinct concerns are combined here:
    - Interest: the user selected or added this language
    - Proficiency: earned through XP from projects/challenges,
                   optionally validated through AI-generated test

    Business Logic Location:
    - XP awarding       → services/language_xp_service.py
    - Test scheduling   → services/language_test_service.py
    - Level calculation → calculate_level_from_xp() (pure, lives here)
    """
    __tablename__ = "user_languages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    language_id = db.Column(
        db.Integer,
        db.ForeignKey("languages.id"),
        nullable=False
    )

    source = db.Column(
        db.Enum('signup', 'self_added', name='user_language_source'),
        nullable=False
    )

    # Language-specific progression
    language_level = db.Column(db.Integer, default=1, nullable=False)
    language_xp = db.Column(db.Integer, default=0, nullable=False)

    # Proficiency test tracking
    last_tested_at = db.Column(db.DateTime, nullable=True)
    test_cooldown_until = db.Column(db.DateTime, nullable=True)

    # Activity tracking
    last_activity_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref("user_languages", lazy="dynamic")
    )
    language = db.relationship("Language")

    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'language_id',
            name='uix_user_language_id'
        ),
    )

    # ===== PURE CALCULATION — belongs in model =====

    @staticmethod
    def calculate_level_from_xp(xp):
        """
        Calculate language level from XP.

        Formula: level = floor(sqrt(xp / 50)) + 1
        Slower curve than account XP (which uses xp / 100).
        Capped at level 100.

        Examples:
            0 XP    → Level 1
            50 XP   → Level 2
            200 XP  → Level 3
            5000 XP → Level 11
        """
        if xp < 0:
            return 1
        level = int(math.sqrt(xp / 50)) + 1
        return min(level, 100)

    def update_level(self):
        """
        Recalculate and update level from current XP.
        Pure field update — no external dependencies.

        Returns:
            tuple: (leveled_up: bool, old_level: int, new_level: int)
        """
        old_level = self.language_level
        self.language_level = self.calculate_level_from_xp(self.language_xp)
        leveled_up = self.language_level > old_level
        return leveled_up, old_level, self.language_level

    def is_on_cooldown(self):
        """
        Check if user is currently in test cooldown period.
        Read-only check — belongs in model.

        Returns:
            bool
        """
        if self.test_cooldown_until is None:
            return False
        cooldown = self.test_cooldown_until
        if cooldown.tzinfo is None:
            cooldown = cooldown.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < cooldown

    def __repr__(self):
        return (
            f"<UserLanguage user_id={self.user_id} "
            f"language_id={self.language_id} "
            f"level={self.language_level}>"
        )