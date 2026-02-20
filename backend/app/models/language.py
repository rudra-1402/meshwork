from app.extensions import db
from datetime import datetime, timezone


class Language(db.Model):
    """
    Reference table for programming languages.
    Seeded at migration time. Not written to by application logic.
    Shared vocabulary across user_languages, project_languages.
    """
    __tablename__ = "languages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Language {self.name}>"