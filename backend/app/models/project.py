"""
Project model - represents collaborative projects in MeshWork.
Schema only. All business logic belongs in project_service.py.
"""
from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
import enum


class ProjectStatus(enum.Enum):
    """Valid project lifecycle states."""
    DRAFT = "Draft"
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class MembershipPolicy(enum.Enum):
    """How users can join this project."""
    OPEN = "open"          # Anyone can join immediately
    REQUEST = "request"    # Join request requires approval
    INVITE = "invite"      # Owner must invite users


class ProjectVisibility(enum.Enum):
    """Who can discover this project."""
    PUBLIC = "public"      # Visible in discovery feed
    PRIVATE = "private"    # Only members can see it


class Project(db.Model):
    __tablename__ = 'projects'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Core metadata
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Creator - never changes, even if they leave
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Project state and access control
    status = db.Column(
        db.Enum(ProjectStatus, name='project_status', create_type=False),
        nullable=False,
        default=ProjectStatus.DRAFT
    )
    membership_policy = db.Column(
        db.Enum(MembershipPolicy, name='project_membership_policy', create_type=False),
        nullable=False,
        default=MembershipPolicy.REQUEST
    )
    visibility = db.Column(
        db.Enum(ProjectVisibility, name='project_visibility', create_type=False),
        nullable=False,
        default=ProjectVisibility.PRIVATE
    )

    # Interest tags (JSON array of strings matching user_scorings.interest_scores keys)
    # Example: ["Web Development", "Machine Learning", "UI/UX Design"]
    interest_tags = db.Column(JSONB, nullable=True)

    # Forking lineage
    forked_from_id = db.Column(
        db.Integer,
        db.ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True
    )
    fork_count = db.Column(db.Integer, nullable=False, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_projects')
    
    # Self-referential for forking
    forked_from = db.relationship(
        'Project',
        remote_side=[id],
        backref='forks',
        foreign_keys=[forked_from_id]
    )

    # Members (via join table)
    members = db.relationship(
        'ProjectMember',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    # Languages (via join table)
    languages = db.relationship(
        'ProjectLanguage',
        back_populates='project',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Project {self.id}: {self.title} ({self.status.value})>'
