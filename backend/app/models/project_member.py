"""
ProjectMember model - join table linking users to projects with roles.
Schema only. All business logic belongs in project_service.py.
"""
from datetime import datetime, timezone
from app.extensions import db
import enum


class ProjectMemberRole(enum.Enum):
    """Member roles within a project."""
    OWNER = "owner"             # Full control, can delete project
    CONTRIBUTOR = "contributor"  # Can edit project content
    VIEWER = "viewer"           # Read-only access
    PENDING = "pending"         # Join request awaiting approval


class ProjectMember(db.Model):
    __tablename__ = 'project_members'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Role
    role = db.Column(
        db.Enum(ProjectMemberRole, name='project_member_role', create_type=False),
        nullable=False,
        default=ProjectMemberRole.PENDING
    )

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

    # Audit trail - who invited this user (nullable for creator)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Unique constraint enforced at DB level
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uix_project_member'),
    )

    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', foreign_keys=[user_id], backref='project_memberships')
    inviter = db.relationship('User', foreign_keys=[invited_by])

    def __repr__(self):
        return f'<ProjectMember project_id={self.project_id} user_id={self.user_id} role={self.role.value}>'
