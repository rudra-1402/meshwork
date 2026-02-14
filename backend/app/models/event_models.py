from app.extensions import db
from datetime import datetime


class Event(db.Model):
    """
    Events system - created by colleges, communities, or verified users.
    Events can have tasks, requirements, and verification.
    
    FUTURE FEATURE - Schema designed for forward compatibility.
    """
    __tablename__ = "events"

    event_id = db.Column(db.Integer, primary_key=True)
    
    # Event basics
    event_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # "hackathon", "workshop", "competition", etc.
    
    # Creator information
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Creator type: "college", "community", "user"
    creator_type = db.Column(db.String(20), nullable=False)
    
    # Creator entity ID (college_id or community_id)
    creator_entity_id = db.Column(db.Integer, nullable=True)
    
    # Event access control
    is_college_specific = db.Column(db.Boolean, default=False)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=True)
    
    # Event requirements (JSON)
    # Example: {
    #   "min_level": 5,
    #   "min_xp": 100,
    #   "required_languages": ["Python", "JavaScript"],
    #   "min_language_proficiency": {"Python": 10, "Java": 5}
    # }
    requirements = db.Column(db.JSON, nullable=True)
    
    # Event settings
    max_participants = db.Column(db.Integer, nullable=True)
    current_participants = db.Column(db.Integer, default=0)
    
    # Programming languages involved
    programming_languages = db.Column(db.JSON, nullable=True)
    
    # Event timing
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    
    # Verification status (admin approval required?)
    requires_verification = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Event status
    status = db.Column(db.String(20), default="draft")  # "draft", "pending", "active", "completed", "cancelled"
    
    # XP/Rewards
    completion_xp = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ===== Relationships =====
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_events")
    college = db.relationship("College", backref="events")
    verifier = db.relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<Event '{self.event_name}'>"
    
    def can_user_participate(self, user):
        """
        Check if user meets requirements to participate.
        
        Args:
            user: User instance
            
        Returns:
            tuple: (can_participate: bool, reason: str)
        """
        # Check verification
        if not self.is_verified:
            return False, "Event not yet verified"
        
        # Check status
        if self.status != "active":
            return False, f"Event is {self.status}"
        
        # Check participant limit
        if self.max_participants and self.current_participants >= self.max_participants:
            return False, "Event is full"
        
        # Check college restriction
        if self.is_college_specific and user.college_id != self.college_id:
            return False, "This event is only for specific college students"
        
        # Check requirements
        if self.requirements:
            # Check user level (from user.level attribute)
            min_level = self.requirements.get('min_level')
            if min_level and hasattr(user, 'level') and user.level < min_level:
                return False, f"Requires level {min_level} (you are level {user.level})"
            
            # Check XP
            min_xp = self.requirements.get('min_xp')
            if min_xp and hasattr(user, 'xp') and user.xp < min_xp:
                return False, f"Requires {min_xp} XP (you have {user.xp} XP)"
            
            # Check language proficiency (requires UserLanguage system)
            lang_requirements = self.requirements.get('min_language_proficiency', {})
            if lang_requirements:
                from app.models.user_language import UserLanguage
                for lang, min_prof in lang_requirements.items():
                    user_lang = UserLanguage.query.filter_by(
                        user_id=user.id,
                        language=lang
                    ).first()
                    
                    if not user_lang or user_lang.language_level < min_prof:
                        return False, f"Requires {lang} level {min_prof}"
        
        return True, "Can participate"


class EventParticipant(db.Model):
    """
    Tracks event participants.
    """
    __tablename__ = "event_participants"

    id = db.Column(db.Integer, primary_key=True)
    
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.event_id"),
        nullable=False
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    registration_status = db.Column(db.String(20), default="registered")  # "registered", "confirmed", "completed", "dropped"
    
    xp_earned = db.Column(db.Integer, default=0)
    
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # ===== Relationships =====
    event = db.relationship("Event", backref="participants")
    user = db.relationship("User", backref="event_participations")
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='uix_user_event_participant'),
    )


class EventTask(db.Model):
    """
    Tasks associated with events (similar to community tasks).
    """
    __tablename__ = "event_tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.event_id"),
        nullable=False
    )
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default="Medium")
    xp_reward = db.Column(db.Integer, default=0)
    
    # Actions (sub-tasks)
    actions = db.Column(db.JSON, nullable=False)
    
    is_required = db.Column(db.Boolean, default=False)  # Required to complete event?
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ===== Relationships =====
    event = db.relationship("Event", backref="tasks")
