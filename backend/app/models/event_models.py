"""
Event Models

Database schema for events, participants, tasks, and task completions.

Architecture:
- Schema ONLY. No business logic, no DB queries, no imports of other models.
- All business logic lives in app/services/event_service.py

Changes from original:
- REMOVED: can_user_participate() — violated architecture contract (business logic +
  inline DB queries on a model). Migrated to EventService.check_user_eligibility().
- REMOVED: current_participants column — replaced by dynamic count via
  EventService.get_event_participants(). See Known Limitations in viva notes.
- ADDED: EventTaskCompletion — tracks per-user, per-action completion within an EventTask.
"""

from app.extensions import db
from datetime import datetime, timezone


class Event(db.Model):
    """
    Events created by colleges, communities, or verified users.

    Creator types:
    - "college"    → college authority, skips pending (draft → active directly)
    - "community"  → community leader, requires approval if college-specific
    - "user"       → regular user, requires approval if college-specific

    Status flow (see VALID_EVENT_TRANSITIONS in event_constants.py):
        draft → pending → active → completed
                       ↘           ↘
                        cancelled   cancelled
    """
    __tablename__ = "events"

    event_id = db.Column(db.Integer, primary_key=True)

    # Event basics
    event_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # "hackathon", "workshop", etc.

    # Creator — dual-identity support
    # created_by: legacy FK to users.id (kept nullable for backward compat with existing rows)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # created_by_user_id: set when creator_type is "user" or "community"
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # created_by_personnel_id: set when creator_type is "college"
    created_by_personnel_id = db.Column(db.Integer, db.ForeignKey("college_personnel.id"), nullable=True)
    creator_type = db.Column(db.String(20), nullable=False)   # EventCreatorType constant
    creator_entity_id = db.Column(db.Integer, nullable=True)  # college_id or community_id

    # Access control
    is_college_specific = db.Column(db.Boolean, default=False)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=True)

    # Participation requirements (JSON)
    # Schema: {
    #   "min_level": int,
    #   "min_xp": int,
    #   "required_languages": [str],
    #   "min_language_proficiency": {lang_name: int}
    # }
    requirements = db.Column(db.JSON, nullable=True)

    # Capacity
    max_participants = db.Column(db.Integer, nullable=True)
    # NOTE: current_participants column removed.
    # Participant count is computed dynamically via EventService.get_event_participants().
    # Known limitation: no row-level lock on capacity check (TOCTOU). Acceptable for v1.

    # Languages relevant to the event
    programming_languages = db.Column(db.JSON, nullable=True)

    # Timing
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)

    # Verification (legacy fields — retained for forward compatibility)
    requires_verification = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Status — governed by VALID_EVENT_TRANSITIONS state machine
    status = db.Column(db.String(20), default="draft", nullable=False)

    # XP awarded to participants on attendance confirmation (additive on top of event_attended constant)
    completion_xp = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ===== Relationships =====
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_events")
    creator_user = db.relationship("User", foreign_keys=[created_by_user_id])
    creator_personnel = db.relationship(
        "CollegePersonnel",
        foreign_keys=[created_by_personnel_id],
        backref=db.backref("created_events", cascade="all, delete")
    )
    college = db.relationship("College", backref="events")
    verifier = db.relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        db.Index('idx_events_created_by', 'created_by'),
        db.Index('idx_events_college_id', 'college_id'),
        db.Index('idx_events_creator_entity_id', 'creator_entity_id'),
        db.Index('idx_events_status', 'status'),
    )

    def __repr__(self):
        return f"<Event '{self.event_name}' [{self.status}]>"


class EventParticipant(db.Model):
    """
    Tracks registration and attendance status for each event-user pair.

    Status flow (see VALID_PARTICIPANT_TRANSITIONS in event_constants.py):
        registered → confirmed → completed
                   ↘           ↘
                    dropped     dropped
    """
    __tablename__ = "event_participants"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(db.Integer, db.ForeignKey("events.event_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Governed by VALID_PARTICIPANT_TRANSITIONS state machine
    registration_status = db.Column(db.String(20), default="registered", nullable=False)

    # Total XP this participant has earned from this event (across all sources)
    xp_earned = db.Column(db.Integer, default=0)

    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # ===== Relationships =====
    event = db.relationship("Event", backref="participants")
    user = db.relationship("User", backref="event_participations")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='uix_user_event_participant'),
    )

    def __repr__(self):
        return f"<EventParticipant user={self.user_id} event={self.event_id} [{self.registration_status}]>"


class EventTask(db.Model):
    """
    Tasks associated with an event. Each task has a list of actions (sub-tasks).

    Actions JSON schema:
        [{"id": 1, "text": "Submit GitHub link", "xp": 10}, ...]

    Each action: id (int), text (str), xp (int).
    Schema is validated by EventService.create_event_task() on creation.
    """
    __tablename__ = "event_tasks"

    task_id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(db.Integer, db.ForeignKey("events.event_id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default="Medium")  # "Easy", "Medium", "Hard"
    xp_reward = db.Column(db.Integer, default=0)

    # JSON array of action objects — validated on creation, not at DB level
    actions = db.Column(db.JSON, nullable=False)

    # If True, participant must complete this task to be marked as event-completed
    is_required = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # ===== Relationships =====
    event = db.relationship("Event", backref="tasks")
    completions = db.relationship("EventTaskCompletion", backref="task", lazy="dynamic")

    def __repr__(self):
        return f"<EventTask '{self.title}' (event={self.event_id})>"


class EventTaskCompletion(db.Model):
    """
    Tracks per-user, per-action completion within an EventTask.

    One record per (user, task, action) triple.
    Mirrors the CommunityTask TaskCompletion pattern.

    Status flow:
        pending_verification → approved
                             ↘ rejected

    v1 stub: submissions are auto-approved by _auto_approve_stub() in EventService.
    The verification engine will replace the stub at a single call site —
    see EventService.submit_task_action() for the TODO marker.

    Fields:
    - reviewed_at / reviewed_by: nullable in v1, populated by verification engine.
    - xp_awarded: 0 until approved; set to action.xp on approval.
    """
    __tablename__ = "event_task_completions"

    id = db.Column(db.Integer, primary_key=True)

    event_task_id = db.Column(db.Integer, db.ForeignKey("event_tasks.task_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Which action within the task's actions JSON array
    action_id = db.Column(db.Integer, nullable=False)

    # Governed by TaskCompletionStatus constants
    status = db.Column(db.String(30), default="pending_verification", nullable=False)

    submitted_at = db.Column(db.DateTime, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # FK to users.id — the authority who reviewed (null until verification engine runs)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # XP awarded to user on approval (0 until approved)
    xp_awarded = db.Column(db.Integer, default=0, nullable=False)

    # ===== Relationships =====
    user = db.relationship("User", foreign_keys=[user_id], backref="event_task_completions")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'event_task_id', 'action_id',
            name='uix_user_task_action'
        ),
    )

    def __repr__(self):
        return (
            f"<EventTaskCompletion user={self.user_id} "
            f"task={self.event_task_id} action={self.action_id} [{self.status}]>"
        )