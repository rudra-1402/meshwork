from app.extensions import db
from datetime import datetime, timezone


class UserScoring(db.Model):
    """
    Core scoring data for each user.
    
    Created once at signup from questionnaire, then updated when:
    - User creates/completes projects (affects interest scores)
    - User participates in events (affects role scores)
    - User works in teams (affects collaboration role scores)
    
    Schema design:
    - All raw role scores stored (for future re-ranking)
    - Top 4 dominant roles stored separately (for quick display)
    - Interest scores stored as dict (flexible for adding new interests)
    - Motivation score is engagement metric (NOT skill level)
    """
    __tablename__ = "user_scorings"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # One scoring record per user (enforced at DB level)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    
    # Engagement metric (0.00-10.00)
    # Measures enthusiasm and drive, NOT technical skill
    # Used for: community activity predictions, team matching
    motivation_score = db.Column(db.Numeric(4, 2), nullable=False)
    
    # Top 3-4 roles as list: ["Builder", "Architect", "Problem Solver", "Collaborator"]
    # These are shown on profile page
    # Recalculated whenever raw_role_scores change significantly
    dominant_roles = db.Column(db.JSON, nullable=False)
    
    # All interest scores as dict: {"Frontend Development": 8.5, "Backend Development": 7.2, ...}
    # Updated when user creates projects with specific tech stacks
    # Used for: project recommendations, team matching, community discovery
    interest_scores = db.Column(db.JSON, nullable=False)
    
    # All raw role scores as dict: {"Builder": 8.5, "Architect": 7.2, "Problem Solver": 8.2, ...}
    # Stored for:
    # - Analytics (how do scores evolve?)
    # - Re-ranking dominant roles (what if 5th role overtakes 4th?)
    # - Future features (role-based recommendations)
    raw_role_scores = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Updated whenever scores change (project activity, events, etc.)
    # NOTE: SQLAlchemy's onupdate with lambda doesn't auto-trigger on JSON column updates
    # Service layer must explicitly update this field
    updated_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationship to User model
    user = db.relationship("User", backref=db.backref("scoring", uselist=False))
    
    def __repr__(self):
        return f"<UserScoring user_id={self.user_id} motivation={self.motivation_score}>"
    
    def get_top_interests(self, n=5):
        """
        Get top N interests by score.
        
        Args:
            n: Number of interests to return (default: 5)
            
        Returns:
            List of dicts: [{"interest": "Backend Development", "score": 8.5}, ...]
        """
        sorted_interests = sorted(
            self.interest_scores.items(),
            key=lambda x: -x[1]  # Sort by score descending
        )
        
        return [
            {"interest": name, "score": float(score)}
            for name, score in sorted_interests[:n]
        ]
    
    def get_role_score(self, role_name):
        """
        Get score for a specific role.
        
        Args:
            role_name: Name of role (e.g., "Builder", "Architect")
            
        Returns:
            Float score (0.00-10.00) or None if role not found
        """
        return self.raw_role_scores.get(role_name)
    
    def is_dominant_role(self, role_name):
        """
        Check if a role is in the user's dominant roles.
        
        Args:
            role_name: Name of role
            
        Returns:
            Boolean
        """
        return role_name in self.dominant_roles
