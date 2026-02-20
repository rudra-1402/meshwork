"""
Skill Service

Manages user skill XP, skill weight validation, and challenge XP distribution.
"""

from app.extensions import db
from app.models.user_skill import UserSkill
from app.constants.gamification import (
    MIN_DOMINANT_SKILL_WEIGHT,
    SKILL_WEIGHT_SUM_TOLERANCE,
    MIN_SKILL_XP_AWARD,
    MAX_SKILL_XP_AWARD,
    AVAILABLE_SKILLS,
)
from datetime import datetime, timezone


class SkillService:
    """
    Centralized skill management service.
    
    Handles:
    - Skill XP awards
    - Challenge XP distribution across skills
    - Skill weight validation
    - Skill leveling
    """
    
    @staticmethod
    def award_skill_xp(user_id, skill_name, amount, source=""):
        """
        Award XP to a specific skill.
        
        Args:
            user_id: User ID
            skill_name: Skill name (e.g., "Python", "React")
            amount: XP to award
            source: Source description (e.g., "challenge", "project")
            
        Returns:
            dict: {
                'success': bool,
                'skill_name': str,
                'xp_added': int,
                'old_xp': int,
                'new_xp': int,
                'leveled_up': bool,
                'old_level': int,
                'new_level': int
            }
        """
        # Validate amount
        if amount < MIN_SKILL_XP_AWARD:
            return {
                'success': False,
                'reason': f'Skill XP must be at least {MIN_SKILL_XP_AWARD}'
            }
        
        if amount > MAX_SKILL_XP_AWARD:
            return {
                'success': False,
                'reason': f'Skill XP cannot exceed {MAX_SKILL_XP_AWARD} in single award'
            }
        
        # Validate skill name
        if skill_name not in AVAILABLE_SKILLS:
            return {
                'success': False,
                'reason': f'Invalid skill: {skill_name}. Must be one of: {", ".join(AVAILABLE_SKILLS[:5])}...'
            }
        
        # Get or create skill
        skill = UserSkill.query.filter_by(
            user_id=user_id,
            skill_name=skill_name
        ).first()
        
        if not skill:
            skill = UserSkill(
                user_id=user_id,
                skill_name=skill_name,
                xp=0,
                level=0
            )
            db.session.add(skill)
        
        # Record old values
        old_xp = skill.xp
        old_level = skill.level
        
        # Update XP
        skill.xp += amount
        skill.last_activity_at = datetime.now(timezone.utc)
        
        # Update level
        leveled_up, _, new_level = skill.update_level()
        
        # Commit
        db.session.commit()
        
        return {
            'success': True,
            'skill_name': skill_name,
            'xp_added': amount,
            'old_xp': old_xp,
            'new_xp': skill.xp,
            'leveled_up': leveled_up,
            'old_level': old_level,
            'new_level': new_level
        }
    
    @staticmethod
    def distribute_challenge_xp(user_id, total_xp, skill_weights):
        """
        Distribute challenge XP across multiple skills based on weights.
        
        Args:
            user_id: User ID
            total_xp: Total XP to distribute
            skill_weights: Dict like {"Python": 50, "HTML": 25, "CSS": 25}
                          (percentages, should sum to 100)
            
        Returns:
            dict: {
                'success': bool,
                'total_xp': int,
                'skills_updated': list of skill results
            }
        """
        # Validate weights first
        valid, error_msg = SkillService.validate_skill_weights(skill_weights)
        
        if not valid:
            return {
                'success': False,
                'reason': error_msg
            }
        
        results = []
        
        for skill_name, percentage in skill_weights.items():
            # Calculate XP for this skill
            skill_xp = int((percentage / 100.0) * total_xp)
            
            # Skip if XP too small
            if skill_xp < MIN_SKILL_XP_AWARD:
                continue
            
            # Award skill XP
            result = SkillService.award_skill_xp(
                user_id=user_id,
                skill_name=skill_name,
                amount=skill_xp,
                source="challenge"
            )
            
            results.append(result)
        
        return {
            'success': True,
            'total_xp': total_xp,
            'skills_updated': results
        }
    
    @staticmethod
    def validate_skill_weights(weights):
        """
        Validate skill weights for a challenge.
        
        Rules:
        1. All weights must sum to 100 (±1% tolerance)
        2. No negative weights
        3. At least one skill must be ≥30% (dominant skill)
        4. All skill names must be valid
        
        Args:
            weights: Dict like {"Python": 50, "HTML": 25, "CSS": 25}
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not weights:
            return False, "Skill weights cannot be empty"
        
        # Check for negative weights
        if any(w < 0 for w in weights.values()):
            return False, "Negative weights not allowed"
        
        # Check sum
        total = sum(weights.values())
        
        if not (100 - SKILL_WEIGHT_SUM_TOLERANCE <= total <= 100 + SKILL_WEIGHT_SUM_TOLERANCE):
            return False, f"Skill weights must sum to 100 (got {total})"
        
        # Check dominant skill
        if max(weights.values()) < MIN_DOMINANT_SKILL_WEIGHT:
            return False, f"Challenge must have a dominant skill (≥{MIN_DOMINANT_SKILL_WEIGHT}%)"
        
        # Check skill names
        invalid_skills = [s for s in weights.keys() if s not in AVAILABLE_SKILLS]
        if invalid_skills:
            return False, f"Invalid skills: {', '.join(invalid_skills)}"
        
        return True, None
    
    @staticmethod
    def normalize_skill_weights(weights):
        """
        Normalize skill weights to sum exactly to 100.
        
        Args:
            weights: Dict like {"Python": 48, "HTML": 27, "CSS": 26}
            
        Returns:
            dict: Normalized weights summing to 100
        """
        total = sum(weights.values())
        
        if total == 0:
            return weights
        
        # Scale to 100
        normalized = {
            skill: round((weight / total) * 100, 1)
            for skill, weight in weights.items()
        }
        
        # Adjust for rounding errors
        current_sum = sum(normalized.values())
        diff = 100 - current_sum
        
        if diff != 0:
            # Add difference to largest weight
            max_skill = max(normalized, key=normalized.get)
            normalized[max_skill] += diff
        
        return normalized
    
    @staticmethod
    def get_user_skill_profile(user_id, limit=10):
        """
        Get user's skill profile for display.
        
        Args:
            user_id: User ID
            limit: Number of top skills to return
            
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
        
        # Top N skills by XP
        top_skills = sorted(all_skills, key=lambda s: s.xp, reverse=True)[:limit]
        
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
    
    @staticmethod
    def get_skill_leaderboard(skill_name, limit=10):
        """
        Get top users for a specific skill.
        
        Args:
            skill_name: Skill name (e.g., "Python")
            limit: Number of users to return
            
        Returns:
            list: Top users with skill XP and level
        """
        if skill_name not in AVAILABLE_SKILLS:
            return []
        
        top_users = (
            UserSkill.query
            .filter_by(skill_name=skill_name)
            .order_by(UserSkill.xp.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                'user_id': s.user_id,
                'username': s.user.username if s.user else 'Unknown',
                'skill_name': s.skill_name,
                'xp': s.xp,
                'level': s.level,
                'last_activity': s.last_activity_at.isoformat() if s.last_activity_at else None
            }
            for s in top_users
        ]
    
    @staticmethod
    def suggest_skill_weights_for_ai(challenge_title, challenge_description):
        """
        Generate a prompt for AI to suggest skill weights.
        
        This method prepares the data for an AI API call (Google Gemini).
        The actual AI call should be made in the routes/service that needs it.
        
        Args:
            challenge_title: Challenge title
            challenge_description: Challenge description
            
        Returns:
            dict: Prompt and metadata for AI call
        """
        prompt = f"""
            Analyze this coding challenge and suggest skill weights (percentages that sum to 100).

            Challenge Title: {challenge_title}

            Challenge Description: {challenge_description}

            Available Skills: {', '.join(AVAILABLE_SKILLS)}

            Rules:
            1. Weights must sum to 100
            2. At least one skill must be ≥30% (dominant skill)
            3. Only suggest 2-4 skills maximum
            4. Focus on skills directly required by the challenge

            Return ONLY a JSON object like:
            {{"Python": 60, "SQL": 30, "Docker": 10}}

            No explanations, no markdown, just JSON.
            """
        
        return {
            'prompt': prompt,
            'available_skills': AVAILABLE_SKILLS,
            'min_dominant_weight': MIN_DOMINANT_SKILL_WEIGHT
        }

    # ===== READ QUERIES (migrated from UserSkill model) =====

    @staticmethod
    def get_user_top_skills(user_id, limit=5):
        """
        Get a user's top skills ordered by XP.

        Args:
            user_id: User ID
            limit: Max skills to return (default 5)

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
        Full skills summary for profile display.

        Args:
            user_id: User ID

        Returns:
            dict: {total_skills, total_skill_xp, top_skills, level_breakdown}
        """
        all_skills = UserSkill.query.filter_by(user_id=user_id).all()

        total_xp = sum(s.xp for s in all_skills)
        top_skills = sorted(all_skills, key=lambda s: s.xp, reverse=True)[:5]

        level_breakdown = {}
        for skill in all_skills:
            key = f"Level {skill.level}"
            level_breakdown[key] = level_breakdown.get(key, 0) + 1

        return {
            "total_skills": len(all_skills),
            "total_skill_xp": total_xp,
            "top_skills": [
                {
                    "skill_name": s.skill_name,
                    "level": s.level,
                    "xp": s.xp,
                    "last_activity": s.last_activity_at.isoformat() if s.last_activity_at else None,
                }
                for s in top_skills
            ],
            "level_breakdown": level_breakdown,
        }