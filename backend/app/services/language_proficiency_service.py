import logging
from datetime import datetime, timezone

from app.extensions import db
from app.models.user_language import UserLanguage
from app.exceptions import ValidationError, LanguageProficiencyError
from app.models.language import Language

logger = logging.getLogger(__name__)


class LanguageProficiencyService:
    """
    Manages user language proficiency tracking.
    
    Handles:
    - Adding XP to languages when user creates/contributes to projects
    - Level calculation and updates
    - Gatekeeping checks for community leadership
    
    Language proficiency is separate from interest scores:
    - Interest score: "How interested are you in Backend Development?" (questionnaire-based)
    - Language proficiency: "How much Python experience do you have?" (activity-based)
    
    Example:
    - User creates project with Python → +50 Python XP
    - Python level increases from 3 → 4
    - User can now create Python communities (requires level 5)
    """
    
    # Supported programming languages
    # Match this to your project creation form
    
    # XP awards for different activities
    XP_AWARDS = {
        "project_creation": 50,      # Creating a project with this language
        "project_contribution": 30,   # Contributing to someone else's project
        "event_participation": 40,    # Participating in event using this language
        "daily_coding": 10,          # Daily coding streak
        "course_completion": 100,    # Completing a course in this language
    }
    
    # Level requirements for community leadership
    COMMUNITY_LEADERSHIP_LEVEL = 5  # Minimum level to create a community for a language
    
    def add_language_xp(self, user_id, language_name, activity_type, xp_override=None):
        """
        Add XP to a user's language proficiency.
        Creates language record if it doesn't exist.

        Args:
            user_id:       User ID
            language_name: Language name string (must exist in languages table)
            activity_type: Type of activity (must be in XP_AWARDS)
            xp_override:   Optional XP amount override

        Returns:
            Dict with old_level, new_level, xp_gained, leveled_up, total_xp

        Raises:
            ValidationError:           If language or activity_type is invalid
            LanguageProficiencyError:  If database update fails
        """
        # Validate language against database — single source of truth
        language = Language.query.filter_by(name=language_name).first()
        if not language:
            raise ValidationError(
                f"Unsupported language: {language_name}. "
                f"Must match an entry in the languages table."
            )

        # Validate activity type and determine XP
        if xp_override is not None:
            xp_to_add = xp_override
        elif activity_type in self.XP_AWARDS:
            xp_to_add = self.XP_AWARDS[activity_type]
        else:
            raise ValidationError(
                f"Unknown activity type: {activity_type}. "
                f"Supported: {', '.join(self.XP_AWARDS.keys())}"
            )

        logger.info(
            f"Adding {xp_to_add} XP to {language_name} for user_id={user_id} "
            f"(activity: {activity_type})"
        )

        try:
            lang_record = UserLanguage.query.filter_by(
                user_id=user_id,
                language_id=language.id
            ).first()

            if not lang_record:
                lang_record = UserLanguage(
                    user_id=user_id,
                    language_id=language.id,
                    source='self_added',
                    language_level=1,
                    language_xp=0
                )
                db.session.add(lang_record)
                logger.info(
                    f"Created new language record: {language_name} "
                    f"for user_id={user_id}"
                )

            # XP logic lives here in the service, not the model
            old_level = lang_record.language_level
            old_xp = lang_record.language_xp

            lang_record.language_xp += xp_to_add
            lang_record.language_level = UserLanguage.calculate_level_from_xp(
                lang_record.language_xp
            )
            lang_record.last_activity_at = datetime.now(timezone.utc)

            leveled_up = lang_record.language_level > old_level

            db.session.commit()

            if leveled_up:
                logger.info(
                    f"User {user_id} leveled up in {language_name}: "
                    f"Level {old_level} → {lang_record.language_level}"
                )

            return {
                "language": language_name,
                "old_level": old_level,
                "new_level": lang_record.language_level,
                "old_xp": old_xp,
                "new_xp": lang_record.language_xp,
                "xp_gained": xp_to_add,
                "leveled_up": leveled_up
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add language XP for user_id={user_id}: {e}")
            raise LanguageProficiencyError(f"Database error: {str(e)}")
    
    def add_language_xp_batch(self, user_id, languages, activity_type):
        """
        Add XP to multiple languages at once.
        Useful when a project uses multiple languages.
        
        Args:
            user_id: User ID
            languages: List of language names
            activity_type: Activity type (same XP for all languages)
            
        Returns:
            List of result dicts (one per language)
            
        Raises:
            ValidationError: If any language is invalid
            LanguageProficiencyError: If database update fails
        """
        results = []
        
        for language in languages:
            result = self.add_language_xp(user_id, language, activity_type)
            results.append(result)
        
        return results
    
    def get_user_language_proficiency(self, user_id, language_name):
        language = Language.query.filter_by(name=language_name).first()
        if not language:
            return None

        lang_record = UserLanguage.query.filter_by(
            user_id=user_id,
            language_id=language.id
        ).first()

        if not lang_record:
            return None

        return {
            "language": language.name,
            "level": lang_record.language_level,
            "xp": lang_record.language_xp,
            "last_activity_at": lang_record.last_activity_at.isoformat()
                if lang_record.last_activity_at else None
        }
    
    def get_all_user_languages(self, user_id, min_level=None):
        query = UserLanguage.query.filter_by(
            user_id=user_id
        ).join(Language, UserLanguage.language_id == Language.id)

        if min_level is not None:
            query = query.filter(UserLanguage.language_level >= min_level)

        query = query.order_by(
            UserLanguage.language_level.desc(),
            UserLanguage.language_xp.desc()
        )

        return [
            {
                "language": record.language.name,
                "level": record.language_level,
                "xp": record.language_xp,
                "last_activity_at": record.last_activity_at.isoformat()
                    if record.last_activity_at else None
            }
            for record in query.all()
        ]
    
    def can_create_community(self, user_id, language_name):
        language = Language.query.filter_by(name=language_name).first()
        if not language:
            return {
                "can_create": False,
                "current_level": 0,
                "required_level": self.COMMUNITY_LEADERSHIP_LEVEL,
                "reason": f"'{language_name}' is not a recognised language."
            }

        lang_record = UserLanguage.query.filter_by(
            user_id=user_id,
            language_id=language.id
        ).first()

        current_level = lang_record.language_level if lang_record else 0
        required_level = self.COMMUNITY_LEADERSHIP_LEVEL
        can_create = current_level >= required_level

        if can_create:
            reason = None
        elif current_level == 0:
            reason = (
                f"You need {language_name} experience to create a "
                f"{language_name} community. "
                f"Create projects using {language_name} to gain proficiency."
            )
        else:
            reason = (
                f"You need {language_name} level {required_level}. "
                f"Your current level: {current_level}."
            )

        return {
            "can_create": can_create,
            "current_level": current_level,
            "required_level": required_level,
            "reason": reason
        }
    
    def get_top_users_by_language(self, language_name, limit=10):
        language = Language.query.filter_by(name=language_name).first()
        if not language:
            return []

        top_users = (
            UserLanguage.query
            .filter_by(language_id=language.id)
            .order_by(
                UserLanguage.language_level.desc(),
                UserLanguage.language_xp.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "user_id": record.user_id,
                "language": language_name,
                "level": record.language_level,
                "xp": record.language_xp
            }
            for record in top_users
        ]
    
    def calculate_xp_to_next_level(self, current_xp):
        """
        Calculate how much XP is needed to reach the next level.
        
        Args:
            current_xp: Current XP amount
            
        Returns:
            Dict with current_level, next_level, xp_needed
        """
        current_level = UserLanguage.calculate_level_from_xp(current_xp)
        
        # Calculate XP needed for next level
        # Reverse engineer from level formula: level = floor(sqrt(xp / 50)) + 1
        # xp = ((level - 1) ^ 2) * 50
        next_level = current_level + 1
        xp_for_next_level = ((next_level - 1) ** 2) * 50
        xp_needed = xp_for_next_level - current_xp
        
        return {
            "current_level": current_level,
            "next_level": next_level,
            "current_xp": current_xp,
            "xp_for_next_level": xp_for_next_level,
            "xp_needed": xp_needed
        }
