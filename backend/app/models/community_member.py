from app.extensions import db
from datetime import datetime

class CommunityMember(db.Model):
    __tablename__ = "community_members"

    member_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.community_id"),
        nullable=False
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # 🔹 Relationships
    user = db.relationship("User", backref="community_memberships")
    community = db.relationship("Community", backref="members")
