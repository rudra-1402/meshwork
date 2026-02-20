from app.extensions import db
from datetime import datetime, timezone


class Community(db.Model):
    __tablename__ = "communities"

    community_id = db.Column(db.Integer, primary_key=True)

    # Which college this community belongs to (if college-specific)
    college_id = db.Column(
        db.Integer,
        db.ForeignKey("colleges.id"),
        nullable=False
    )

    community_name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Creator (Admin)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # ===== NEW: Community Settings =====
    
    # Member limits
    max_members = db.Column(db.Integer, default=50, nullable=False)
    current_member_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Access control
    is_college_specific = db.Column(db.Boolean, default=True, nullable=False)
    # If True: only users from same college can join
    # If False: anyone can join
    
    # Programming languages (multi-select JSON array)
    # Example: ["Python", "Java", "JavaScript"]
    programming_languages = db.Column(db.JSON, nullable=True)
    
    # Community status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    
    # Additional settings (flexible JSON for future expansion)
    # Can store: {"require_approval": false, "allow_file_sharing": true, ...}
    settings = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ===== Relationships =====
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_communities")
    college = db.relationship("College", backref="communities")

    __table_args__ = (
        db.Index('idx_community_college_id', 'college_id'),
    )
    
    def __repr__(self):
        return f"<Community {self.community_name}>"
    
    def is_full(self):
        """Check if community has reached member limit"""
        return self.current_member_count >= self.max_members
    
    # Eligibility check → CommunityService.can_user_join(community, user)

    def increment_member_count(self):
        """Increment member count atomically at DB level (called when user joins)"""
        db.session.execute(
            db.update(Community).where(
                Community.community_id == self.community_id
            ).values(current_member_count=Community.current_member_count + 1)
        )
    
    def decrement_member_count(self):
        """Decrement member count (called when user leaves)"""
        if self.current_member_count > 0:
            self.current_member_count -= 1