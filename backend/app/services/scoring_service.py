import json
import os
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai
from google.genai import types

from app.extensions import db
from app.models.scoring import UserScoring
from app.models.user import User
from app.models.scoring_history import ScoringHistory
from app.exceptions import (
    ValidationError, 
    AlreadyScoredError, 
    ScoringError,
    NotScoredError
)
from app.schemas.questionnaire_schema import validate_questionnaire, get_questionnaire_summary

logger = logging.getLogger(__name__)


class ScoringService:
    """
    Handles AI-powered scoring of users based on questionnaire responses.
    
    Two distinct workflows:
    1. Initial scoring from signup questionnaire (one-time, creates record)
    2. Score updates from user activity (ongoing, updates existing record)
    
    Scores users on:
    - 10 collaboration roles (internal signals for matching)
    - 32 technical interests (displayed and used for recommendations)
    - 1 motivation score (engagement metric, not skill)
    """
    
    # Role definitions (internal signals, not shown to users directly)
    ROLES = [
        "Builder", "Architect", "Problem Solver", "Specialist", "Designer",
        "Product Thinker", "Leader", "Collaborator", "Mentor", "Explorer"
    ]
    
    # Interest definitions (scores stored and used for matching)
    INTERESTS = [
        "Frontend Development", "Backend Development", "Full-Stack Development",
        "Mobile App Development", "Systems Programming", "Game Development",
        "DevOps & Infrastructure", "Cybersecurity", "Data Structures & Algorithms",
        "Competitive Programming", "Machine Learning", "Artificial Intelligence (Applied)",
        "Data Science", "Computer Vision", "Natural Language Processing",
        "API Design", "Distributed Systems", "Cloud Computing", "Database Design",
        "Performance Optimization", "UI/UX Design", "Product Engineering",
        "Developer Experience (DX)", "Hackathons", "Open Source Contribution",
        "Startup Projects", "Research-Oriented Projects", "Teaching / Mentorship",
        "Leadership & Team Management", "Rapid Prototyping", "Long-Term Projects",
        "Experimentation / Side Projects"
    ]
    
    # Scoring constants
    NUM_DOMINANT_ROLES = 4  # Always select top 4 roles
    
    def __init__(self):
        """Initialize Google Gemini client with API key"""
        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set.\n"
                "Get your API key from: https://aistudio.google.com/app/apikey\n"
                "Then set it with: export GEMINI_API_KEY='your-key-here'"
            )
        
        # Initialize client with API key
        self.client = genai.Client(api_key=api_key)
        
        # Use Gemini 3 Flash Preview (fast and cheap) or Gemini 3 Pro Preview (more capable)
        # Flash is recommended for this use case - much faster and cheaper
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        
        logger.info(f"Gemini client configured with model={self.model_name}")
        
        # Verify API key works
        self._verify_api_access()
    
    def _verify_api_access(self):
        """Verify that Gemini API is accessible with provided key"""
        try:
            # Test with a simple prompt
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Say 'OK'"
            )
            logger.info(f"Gemini API verified successfully: {response.text[:50]}")
        except Exception as e:
            logger.error(f"Failed to verify Gemini API access: {e}")
            raise ValueError(
                f"Gemini API verification failed: {str(e)}\n"
                "Check that your GEMINI_API_KEY is valid"
            )
    
    def process_initial_questionnaire(self, user_id, questionnaire_data):
        """
        Process INITIAL user questionnaire responses at signup.
        This is ONE-TIME ONLY. Raises AlreadyScoredError if user already has scores.
        
        Args:
            user_id: ID of the user being scored
            questionnaire_data: Dict containing user's questionnaire responses
            
        Returns:
            Dict with:
            - dominant_roles: List of 4 role names
            - motivation_score: Float 0.00-10.00
            - top_interests: List of top 5 interests with scores
            
        Raises:
            AlreadyScoredError: If user has already completed questionnaire
            ValidationError: If questionnaire data is invalid
            ScoringError: If AI scoring fails
            Exception: If database errors occur
        """
        start_time = time.time()
        logger.info(f"Processing initial questionnaire for user_id={user_id}")
        
        # ✅ CRITICAL: Enforce one-time submission
        existing_scoring = UserScoring.query.filter_by(user_id=user_id).first()
        if existing_scoring:
            logger.warning(f"Attempted duplicate initial scoring for user_id={user_id}")
            raise AlreadyScoredError(
                f"User {user_id} has already completed the initial questionnaire"
            )
        
        # Validate questionnaire structure
        try:
            validate_questionnaire(questionnaire_data)
            logger.info(f"Questionnaire validated for user_id={user_id}: {get_questionnaire_summary(questionnaire_data)}")
        except ValidationError as e:
            logger.error(f"Questionnaire validation failed for user_id={user_id}: {e}")
            raise
        
        try:
            # 1. Build scoring prompt
            prompt = self._build_scoring_prompt(questionnaire_data)
            
            # 2. Call Gemini with retry logic
            raw_response = self._call_gemini(prompt)
            
            # 3. Parse JSON response
            raw_output = json.loads(raw_response)
            
            # 4. Validate AI response structure and ranges
            validated_output = self._validate_ai_response(raw_output)
            
            # 5. Apply statistical normalization
            normalized_output = self._normalize_scores(validated_output)
            
            # 6. Select top 4 dominant roles (deterministic)
            dominant_roles = self._select_dominant_roles(normalized_output['roles'])
            
            # 7. Persist to database with history
            self._persist_initial_scoring(
                user_id=user_id,
                motivation_score=normalized_output['motivation_score'],
                interest_scores=normalized_output['interests'],
                dominant_roles=dominant_roles,
                raw_role_scores=normalized_output['roles']
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"Initial scoring completed for user_id={user_id} in {elapsed:.2f}s, "
                f"dominant_roles={dominant_roles}"
            )
            
            # Return comprehensive result
            return {
                "dominant_roles": dominant_roles,
                "motivation_score": float(normalized_output['motivation_score']),
                "top_interests": self._get_top_n_from_dict(normalized_output['interests'], n=5)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI for user_id={user_id}: {e}")
            logger.error(f"Raw AI response: {raw_response if 'raw_response' in locals() else 'N/A'}")
            raise ScoringError(f"AI returned invalid JSON: {e}")
        except (ValidationError, AlreadyScoredError):
            # Re-raise these as-is
            raise
        except Exception as e:
            logger.error(f"Initial scoring failed for user_id={user_id}: {e}", exc_info=True)
            raise ScoringError(f"Scoring service error: {str(e)}")
    
    def update_interest_scores_from_activity(self, user_id, activity_type, 
                                            activity_data, interest_adjustments):
        """
        Update interest scores based on user activity (project creation, events, etc.)
        
        This is separate from initial scoring and can be called multiple times.
        Used when user creates projects with specific tech stacks.
        
        Args:
            user_id: User ID
            activity_type: Type of activity ("project_creation", "event_participation", etc.)
            activity_data: Dict with activity details (for logging)
            interest_adjustments: Dict mapping interest names to score deltas
                Example: {"Frontend Development": 0.5, "Backend Development": 0.3}
        
        Returns:
            Dict with updated interest scores and changes
            
        Raises:
            NotScoredError: If user hasn't completed initial questionnaire
            ValidationError: If interest names are invalid
        """
        logger.info(f"Updating interest scores for user_id={user_id}, activity={activity_type}")
        
        # Must have completed initial scoring
        scoring_record = UserScoring.query.filter_by(user_id=user_id).first()
        if not scoring_record:
            raise NotScoredError(
                f"User {user_id} has not completed initial questionnaire. "
                f"Cannot update interest scores."
            )
        
        # Validate interest names
        invalid_interests = [
            interest for interest in interest_adjustments.keys()
            if interest not in self.INTERESTS
        ]
        if invalid_interests:
            raise ValidationError(f"Invalid interest names: {invalid_interests}")
        
        # Capture old state for history
        old_scores = {
            "interests": scoring_record.interest_scores.copy(),
            "dominant_roles": scoring_record.dominant_roles.copy(),
            "roles": scoring_record.raw_role_scores.copy(),
            "motivation": float(scoring_record.motivation_score)
        }
        
        # Apply adjustments (with capping at 10.0)
        for interest, delta in interest_adjustments.items():
            current_score = scoring_record.interest_scores.get(interest, 0.0)
            new_score = min(10.0, max(0.0, current_score + delta))
            scoring_record.interest_scores[interest] = round(new_score, 2)
        
        # Update timestamp (SQLAlchemy doesn't auto-update for JSON changes)
        from datetime import datetime, timezone
        scoring_record.updated_at = datetime.now(timezone.utc)
        
        # Prepare new state
        new_scores = {
            "interests": scoring_record.interest_scores.copy(),
            "dominant_roles": scoring_record.dominant_roles.copy(),
            "roles": scoring_record.raw_role_scores.copy(),
            "motivation": float(scoring_record.motivation_score)
        }
        
        # Create history entry
        event_description = self._format_activity_description(activity_type, activity_data)
        history_entry = ScoringHistory.create_from_score_update(
            user_id=user_id,
            event_type=activity_type,
            event_description=event_description,
            old_scores=old_scores,
            new_scores=new_scores
        )
        
        db.session.add(history_entry)
        db.session.commit()
        
        logger.info(f"Interest scores updated for user_id={user_id}: {interest_adjustments}")
        
        return {
            "updated_interests": interest_adjustments,
            "top_interests": self._get_top_n_from_dict(scoring_record.interest_scores, n=5)
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_gemini(self, prompt):
        """
        Call Google Gemini API with retry logic for transient failures.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            JSON string from model response
            
        Raises:
            ScoringError: After 3 failed attempts or on API errors
        """
        try:
            logger.info(f"Calling Gemini model '{self.model_name}'")
            
            # Configure generation parameters
            config = types.GenerateContentConfig(
                temperature=0.3,  # Lower = more consistent/conservative scoring
                top_p=0.9,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"  # Request JSON output
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Extract text
            if not response.text:
                logger.error("Gemini returned empty response")
                raise ScoringError("Empty response from Gemini")
            
            content = response.text.strip()
            
            # Clean up markdown code blocks if present (just in case)
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            logger.info(f"Successfully received response from Gemini ({len(content)} chars)")
            return content
            
        except ScoringError:
            # Re-raise ScoringError as-is
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            raise ScoringError(f"Gemini API call failed: {str(e)}")
    
    def _validate_ai_response(self, raw_output):
        """
        Validate AI scoring output structure, types, and value ranges.
        
        Args:
            raw_output: Parsed JSON dict from AI
            
        Returns:
            Validated output dict
            
        Raises:
            ValidationError: If validation fails with diagnostic message
        """
        # Check top-level keys
        required_keys = {'motivation_score', 'roles', 'interests'}
        if not required_keys.issubset(raw_output.keys()):
            missing = required_keys - raw_output.keys()
            raise ValidationError(f"AI response missing keys: {missing}")
        
        # Validate motivation score
        motivation = raw_output['motivation_score']
        if not isinstance(motivation, (int, float)):
            raise ValidationError(f"motivation_score must be numeric, got {type(motivation).__name__}")
        if not (0.0 <= motivation <= 10.0):
            raise ValidationError(f"motivation_score {motivation} out of range [0.0, 10.0]")
        
        # Validate roles structure
        if not isinstance(raw_output['roles'], dict):
            raise ValidationError("'roles' must be a dict")
        
        if set(raw_output['roles'].keys()) != set(self.ROLES):
            missing = set(self.ROLES) - set(raw_output['roles'].keys())
            extra = set(raw_output['roles'].keys()) - set(self.ROLES)
            error_msg = []
            if missing:
                error_msg.append(f"missing roles: {missing}")
            if extra:
                error_msg.append(f"unexpected roles: {extra}")
            raise ValidationError(f"Role mismatch - {', '.join(error_msg)}")
        
        for role_name, score in raw_output['roles'].items():
            if not isinstance(score, (int, float)):
                raise ValidationError(f"Role '{role_name}' score must be numeric, got {type(score).__name__}")
            if not (0.0 <= score <= 10.0):
                raise ValidationError(f"Role '{role_name}' score {score} out of range [0.0, 10.0]")
        
        # Validate interests structure
        if not isinstance(raw_output['interests'], dict):
            raise ValidationError("'interests' must be a dict")
        
        if set(raw_output['interests'].keys()) != set(self.INTERESTS):
            missing = set(self.INTERESTS) - set(raw_output['interests'].keys())
            extra = set(raw_output['interests'].keys()) - set(self.INTERESTS)
            error_msg = []
            if missing:
                error_msg.append(f"missing interests: {missing}")
            if extra:
                error_msg.append(f"unexpected interests: {extra}")
            raise ValidationError(f"Interest mismatch - {', '.join(error_msg)}")
        
        for interest_name, score in raw_output['interests'].items():
            if not isinstance(score, (int, float)):
                raise ValidationError(f"Interest '{interest_name}' score must be numeric, got {type(score).__name__}")
            if not (0.0 <= score <= 10.0):
                raise ValidationError(f"Interest '{interest_name}' score {score} out of range [0.0, 10.0]")
        
        return raw_output
    
    def _normalize_scores(self, raw_output):
        """
        Apply statistical normalization to prevent AI score inflation.
        
        Enforces:
        - Total role score sum stays within 50-70 range (average 5.0-7.0 per role)
        - No more than 2 roles can score above 8.0
        - Rounds all scores to 2 decimal places
        
        Args:
            raw_output: Validated AI output
            
        Returns:
            Normalized output dict
        """
        roles = raw_output['roles'].copy()
        
        # Check total role score
        total_role_score = sum(roles.values())
        target_total = 60.0  # Middle of 50-70 range
        
        if total_role_score > 70.0:
            # Scale down all roles proportionally
            scale_factor = target_total / total_role_score
            roles = {k: round(v * scale_factor, 2) for k, v in roles.items()}
            logger.warning(
                f"Normalized inflated role scores: {total_role_score:.1f} → {sum(roles.values()):.1f}"
            )
        
        # Cap number of high scores
        high_scores = sorted(
            [(role, score) for role, score in roles.items() if score > 8.0],
            key=lambda x: -x[1]  # Sort by score descending
        )
        
        if len(high_scores) > 2:
            logger.warning(f"AI assigned {len(high_scores)} roles > 8.0, capping to top 2")
            # Reduce 3rd+ highest scores to 7.9
            for role, score in high_scores[2:]:
                roles[role] = 7.9
        
        # Round all scores
        roles = {k: round(v, 2) for k, v in roles.items()}
        interests = {k: round(v, 2) for k, v in raw_output['interests'].items()}
        motivation = round(raw_output['motivation_score'], 2)
        
        return {
            'roles': roles,
            'interests': interests,
            'motivation_score': motivation
        }
    
    def _select_dominant_roles(self, role_scores):
        """
        Select top 4 dominant roles with deterministic tie-breaking.
        
        Args:
            role_scores: Dict mapping role names to scores
            
        Returns:
            List of 4 role names in descending order of score
        """
        # Sort by score DESC, then alphabetically ASC for deterministic tie-breaking
        sorted_roles = sorted(
            role_scores.items(),
            key=lambda x: (-x[1], x[0])  # Negative score for DESC, name for ASC
        )
        
        # Always select exactly top 4
        dominant_roles = [role for role, score in sorted_roles[:self.NUM_DOMINANT_ROLES]]
        
        return dominant_roles
    
    def _persist_initial_scoring(self, user_id, motivation_score, interest_scores, 
                                dominant_roles, raw_role_scores):
        """
        Persist initial scoring record to database with history entry.
        
        Args:
            user_id: User ID
            motivation_score: Float 0.00-10.00
            interest_scores: Dict of interest scores
            dominant_roles: List of 4 role names
            raw_role_scores: Dict of all role scores
            
        Raises:
            Exception: If database commit fails (with rollback)
        """
        try:
            # Create scoring record
            scoring_record = UserScoring(
                user_id=user_id,
                motivation_score=motivation_score,
                interest_scores=interest_scores,
                dominant_roles=dominant_roles,
                raw_role_scores=raw_role_scores
            )
            
            db.session.add(scoring_record)
            
            # Create initial history entry
            history_entry = ScoringHistory.create_from_initial_scoring(
                user_id=user_id,
                dominant_roles=dominant_roles,
                motivation_score=motivation_score,
                raw_role_scores=raw_role_scores,
                interest_scores=interest_scores
            )

            # Mark questionnaire as completed
            user = User.query.get(user_id)
            if user:
                user.has_completed_questionnaire = True
            
            db.session.add(history_entry)
            db.session.commit()
            
            logger.info(f"Persisted initial scoring for user_id={user_id}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error persisting scores for user_id={user_id}: {e}", exc_info=True)
            raise
    
    def _get_top_n_from_dict(self, scores_dict, n=5):
        """
        Extract top N items from a score dictionary.
        
        Args:
            scores_dict: Dict mapping names to scores
            n: Number of top items to return
            
        Returns:
            List of dicts with 'name' and 'score' keys, sorted by score DESC
        """
        sorted_items = sorted(
            scores_dict.items(),
            key=lambda x: (-x[1], x[0])  # Score DESC, name ASC for ties
        )
        
        return [
            {"name": name, "score": float(score)}
            for name, score in sorted_items[:n]
        ]
    
    def _format_activity_description(self, activity_type, activity_data):
        """
        Format human-readable description of activity for history logging.
        
        Args:
            activity_type: Type of activity
            activity_data: Activity details
            
        Returns:
            Formatted string
        """
        if activity_type == "project_creation":
            return (
                f"Created project: {activity_data.get('project_name', 'Unknown')} "
                f"({', '.join(activity_data.get('languages', []))})"
            )
        elif activity_type == "project_completion":
            return f"Completed project: {activity_data.get('project_name', 'Unknown')}"
        elif activity_type == "event_participation":
            return f"Participated in event: {activity_data.get('event_name', 'Unknown')}"
        else:
            return f"Activity: {activity_type}"
    
    def _build_scoring_prompt(self, responses):
        """
        Build comprehensive AI scoring prompt with rubrics and constraints.
        
        Args:
            responses: Dict containing user's questionnaire responses
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an expert technical recruiter evaluating a software engineering student's profile based on their questionnaire responses.

USER RESPONSES:
{json.dumps(responses, indent=2)}

SCORING TASK:
Score the user on {len(self.ROLES)} collaboration roles, {len(self.INTERESTS)} technical interests, and overall motivation.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL SCORING RULES
═══════════════════════════════════════════════════════════════════════════════

1. MOTIVATION SCORE (0.00-10.00):
   • Measures ENGAGEMENT and DRIVE only — NOT skill level or experience
   • Scoring rubric:
     - 9.0-10.0: Multiple specific examples of self-driven projects, consistent learning habits, clear long-term vision
     - 7.0-8.9: Clear evidence of initiative with 2-3 concrete examples (completed projects, regular practice)
     - 5.0-6.9: Expresses interest with 1 concrete example or consistent activity
     - 3.0-4.9: Vague interest statements or aspirational goals without evidence
     - 0.0-2.9: Minimal engagement, contradictory statements, or no clear drive

2. ROLE SCORES (0.00-10.00 each):
   • Score conservatively based on DEMONSTRATED BEHAVIOR, not aspirations or self-labels
   • Each role requires specific behavioral evidence:
   
   Scoring rubric per role:
     - 9.0-10.0: 3+ specific, detailed examples showing mastery of this role
     - 7.0-8.9: 2 clear examples with concrete outcomes
     - 5.0-6.9: 1 solid example with details
     - 3.0-4.9: Mentioned role or implied behavior, but no specific examples
     - 0.0-2.9: No evidence or contradicts role characteristics
   
   PENALTIES (apply cumulatively):
     - Uses buzzwords without context (e.g., "passionate", "innovative"): -2.0 per instance
     - Contradictory statements within responses: -3.0
     - Generic/template-like answers with no personalization: cap at 6.0 maximum
     - Claims experience in >5 roles without evidence: reduce all by -1.5

3. INTEREST SCORES (0.00-10.00 each):
   • Based on EXPERIENCE + demonstrated enthusiasm (not just mention)
   
   Scoring rubric per interest:
     - 9.0-10.0: Built multiple projects, deep study, can discuss technical details
     - 7.0-8.9: Built 1-2 projects OR studied formally with evidence
     - 5.0-6.9: Some hands-on exposure OR strong stated interest with learning plan
     - 3.0-4.9: Mentioned casually or tangentially related experience
     - 0.0-2.9: No evidence or only aware of term

═══════════════════════════════════════════════════════════════════════════════
ROLES TO SCORE (score ALL {len(self.ROLES)} roles):
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(self.ROLES, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
INTERESTS TO SCORE (score ALL {len(self.INTERESTS)} interests):
═══════════════════════════════════════════════════════════════════════════════
{json.dumps(self.INTERESTS, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
STATISTICAL CONSTRAINTS (enforce strictly):
═══════════════════════════════════════════════════════════════════════════════
- Most users should score 4.0-7.0 on most dimensions (this is normal)
- Scores of 9.0+ are EXCEPTIONAL and require extraordinary, specific evidence
- If no evidence exists for a role/interest, score 2.0-3.0 (not 0, but very low)
- Total sum of all 10 role scores should typically be 50-70 (average 5.0-7.0 per role)
- Fewer than 20% of interests should score above 7.0 for typical students
- Be skeptical of broad claims — specificity and examples are required for high scores

═══════════════════════════════════════════════════════════════════════════════
CRITICAL: OUTPUT MUST BE VALID JSON ONLY - NO OTHER TEXT
═══════════════════════════════════════════════════════════════════════════════
Return ONLY a JSON object with this exact structure (no markdown, no explanations):

{{
    "motivation_score": <float between 0.00 and 10.00>,
    "roles": {{
        "Builder": <float>,
        "Architect": <float>,
        "Problem Solver": <float>,
        "Specialist": <float>,
        "Designer": <float>,
        "Product Thinker": <float>,
        "Leader": <float>,
        "Collaborator": <float>,
        "Mentor": <float>,
        "Explorer": <float>
    }},
    "interests": {{
        "Frontend Development": <float>,
        "Backend Development": <float>,
        "Full-Stack Development": <float>,
        "Mobile App Development": <float>,
        "Systems Programming": <float>,
        "Game Development": <float>,
        "DevOps & Infrastructure": <float>,
        "Cybersecurity": <float>,
        "Data Structures & Algorithms": <float>,
        "Competitive Programming": <float>,
        "Machine Learning": <float>,
        "Artificial Intelligence (Applied)": <float>,
        "Data Science": <float>,
        "Computer Vision": <float>,
        "Natural Language Processing": <float>,
        "API Design": <float>,
        "Distributed Systems": <float>,
        "Cloud Computing": <float>,
        "Database Design": <float>,
        "Performance Optimization": <float>,
        "UI/UX Design": <float>,
        "Product Engineering": <float>,
        "Developer Experience (DX)": <float>,
        "Hackathons": <float>,
        "Open Source Contribution": <float>,
        "Startup Projects": <float>,
        "Research-Oriented Projects": <float>,
        "Teaching / Mentorship": <float>,
        "Leadership & Team Management": <float>,
        "Rapid Prototyping": <float>,
        "Long-Term Projects": <float>,
        "Experimentation / Side Projects": <float>
    }}
}}"""