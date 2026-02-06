from app.extensions import db
from datetime import datetime

class Community(db.Model):
    __tablename__ = "communities"

    community_id = db.Column(db.Integer, primary_key=True)

    # Which college this community belongs to
    college_id = db.Column(
        db.Integer,
        db.ForeignKey("colleges.id"),
        nullable=False
    )

    community_name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(150), nullable=False)

    # Creator (Admin)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # 🔹 Relationships (Future-proof)
    creator = db.relationship("User", backref="created_communities")
    college = db.relationship("College", backref="communities")
