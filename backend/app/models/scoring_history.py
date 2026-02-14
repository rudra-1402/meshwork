from app.extensions import db
from datetime import datetime, timezone


class ScoringHistory(db.Model):
    """
    Audit trail for all scoring changes.
    Logs what changed, when, and why (initial questionnaire, project completion, event, etc.)
    
    Use cases:
    - Transparency: "Why did my Builder score increase?"
    - Analytics: "How do scores evolve over time?"
    - Debugging: "Did this project actually affect interest scores?"
    - Academic defense: "Our system maintains full audit trail"
    """
    __tablename__ = "scoring_history"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Event that triggered the score change
    event_type = db.Column(db.String(50), nullable=False)
    # Values: "initial_questionnaire", "project_creation", "project_completion",
    #         "event_participation", "team_collaboration", "manual_adjustment"
    
    # Human-readable description of what happened
    event_description = db.Column(db.Text, nullable=True)
    # Examples:
    # - "Initial questionnaire submitted"
    # - "Created project: AI Chatbot (Python, Flask, NLP)"
    # - "Completed hackathon: 48h Web Dev Challenge"
    
    # Reference to related entity (optional)
    related_entity_type = db.Column(db.String(50), nullable=True)  # "project", "event", etc.
    related_entity_id = db.Column(db.Integer, nullable=True)  # ID of that entity
    
    # What changed (JSON for flexibility)
    changes = db.Column(db.JSON, nullable=False)
    # Structure:
    # {
    #   "roles": {"Builder": {"old": 7.2, "new": 7.8}, ...},
    #   "interests": {"Backend Development": {"old": 6.5, "new": 7.1}, ...},
    #   "motivation": {"old": 8.0, "new": 8.0},
    #   "dominant_roles": {
    #     "old": ["Builder", "Problem Solver", "Collaborator", "Architect"],
    #     "new": ["Builder", "Architect", "Problem Solver", "Collaborator"]
    #   }
    # }
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to User model
    user = db.relationship("User", backref=db.backref("scoring_history", lazy="dynamic"))
    
    # Index for efficient queries
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_event_type', 'event_type'),
    )
    
    def __repr__(self):
        return f"<ScoringHistory user_id={self.user_id} event={self.event_type} at={self.created_at}>"
    
    @staticmethod
    def create_from_initial_scoring(user_id, dominant_roles, motivation_score, 
                                    raw_role_scores, interest_scores):
        """
        Create history entry for initial questionnaire submission.
        
        Args:
            user_id: User ID
            dominant_roles: List of 4 role names
            motivation_score: Float 0-10
            raw_role_scores: Dict of all role scores
            interest_scores: Dict of all interest scores
            
        Returns:
            ScoringHistory instance (not yet committed)
        """
        return ScoringHistory(
            user_id=user_id,
            event_type="initial_questionnaire",
            event_description="Initial questionnaire submitted during signup",
            changes={
                "roles": {role: {"old": None, "new": score} for role, score in raw_role_scores.items()},
                "interests": {interest: {"old": None, "new": score} for interest, score in interest_scores.items()},
                "motivation": {"old": None, "new": float(motivation_score)},
                "dominant_roles": {"old": None, "new": dominant_roles}
            }
        )
    
    @staticmethod
    def create_from_score_update(user_id, event_type, event_description,
                                old_scores, new_scores, 
                                related_entity_type=None, related_entity_id=None):
        """
        Create history entry for score updates (project completion, events, etc.)
        
        Args:
            user_id: User ID
            event_type: Type of event ("project_completion", "event_participation", etc.)
            event_description: Human-readable description
            old_scores: Dict with old state (roles, interests, motivation, dominant_roles)
            new_scores: Dict with new state (same structure)
            related_entity_type: Optional entity type ("project", "event")
            related_entity_id: Optional entity ID
            
        Returns:
            ScoringHistory instance (not yet committed)
        """
        # Calculate what actually changed
        changes = {}
        
        # Role changes
        if "roles" in old_scores and "roles" in new_scores:
            role_changes = {}
            for role, new_score in new_scores["roles"].items():
                old_score = old_scores["roles"].get(role)
                if old_score != new_score:
                    role_changes[role] = {"old": old_score, "new": new_score}
            if role_changes:
                changes["roles"] = role_changes
        
        # Interest changes
        if "interests" in old_scores and "interests" in new_scores:
            interest_changes = {}
            for interest, new_score in new_scores["interests"].items():
                old_score = old_scores["interests"].get(interest)
                if old_score != new_score:
                    interest_changes[interest] = {"old": old_score, "new": new_score}
            if interest_changes:
                changes["interests"] = interest_changes
        
        # Motivation changes
        if "motivation" in old_scores and "motivation" in new_scores:
            if old_scores["motivation"] != new_scores["motivation"]:
                changes["motivation"] = {
                    "old": old_scores["motivation"],
                    "new": new_scores["motivation"]
                }
        
        # Dominant role changes
        if "dominant_roles" in old_scores and "dominant_roles" in new_scores:
            if old_scores["dominant_roles"] != new_scores["dominant_roles"]:
                changes["dominant_roles"] = {
                    "old": old_scores["dominant_roles"],
                    "new": new_scores["dominant_roles"]
                }
        
        return ScoringHistory(
            user_id=user_id,
            event_type=event_type,
            event_description=event_description,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            changes=changes
        )
    
    def get_summary(self):
        """
        Generate human-readable summary of changes.
        
        Returns:
            String summary like "Builder ↑0.6, Frontend Development ↑0.5"
        """
        summary_parts = []
        
        # Role changes
        if "roles" in self.changes:
            for role, change in self.changes["roles"].items():
                old = change.get("old", 0)
                new = change["new"]
                diff = new - (old or 0)
                if diff > 0:
                    summary_parts.append(f"{role} ↑{diff:.1f}")
                elif diff < 0:
                    summary_parts.append(f"{role} ↓{abs(diff):.1f}")
        
        # Interest changes (only show top 2)
        if "interests" in self.changes:
            interest_changes = []
            for interest, change in self.changes["interests"].items():
                old = change.get("old", 0)
                new = change["new"]
                diff = new - (old or 0)
                if diff != 0:
                    interest_changes.append((interest, diff))
            
            # Sort by magnitude of change
            interest_changes.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for interest, diff in interest_changes[:2]:
                if diff > 0:
                    summary_parts.append(f"{interest} ↑{diff:.1f}")
                else:
                    summary_parts.append(f"{interest} ↓{abs(diff):.1f}")
        
        return ", ".join(summary_parts) if summary_parts else "No changes"
