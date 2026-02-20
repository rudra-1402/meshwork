"""
ProjectLanguage model - join table linking projects to programming languages.
Schema only. All business logic belongs in project_service.py.
"""
from datetime import datetime, timezone
from app.extensions import db


class ProjectLanguage(db.Model):
    __tablename__ = 'project_languages'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=False)

    # Timestamp
    created_at = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

    # Unique constraint enforced at DB level
    __table_args__ = (
        db.UniqueConstraint('project_id', 'language_id', name='uix_project_language'),
    )

    # Relationships
    project = db.relationship('Project', back_populates='languages')
    language = db.relationship('Language', backref='project_languages')

    def __repr__(self):
        return f'<ProjectLanguage project_id={self.project_id} language_id={self.language_id}>'
