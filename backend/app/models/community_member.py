from app.extensions import db
from datetime import datetime, timezone

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
        default=lambda: datetime.now(timezone.utc)
    )

    # 🔹 Relationships
    user = db.relationship("User", backref="community_memberships")
    community = db.relationship("Community", backref="members")

    def __repr__(self):
        return f"<CommunityMember user_id={self.user_id} community_id={self.community_id}>"

    __table_args__ = (
        # Prevents duplicate memberships that would corrupt current_member_count
        db.UniqueConstraint('user_id', 'community_id', name='uix_community_member'),
        db.Index('idx_community_member_community_id', 'community_id'),
    )