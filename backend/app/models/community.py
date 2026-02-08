from app.extensions import db
from datetime import datetime


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
        default=datetime.utcnow
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ===== Relationships =====
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_communities")
    college = db.relationship("College", backref="communities")
    
    def __repr__(self):
        return f"<Community {self.community_name}>"
    
    def is_full(self):
        """Check if community has reached member limit"""
        return self.current_member_count >= self.max_members
    
    def can_user_join(self, user):
        """
        Check if a user is eligible to join this community.
        
        Args:
            user: User instance
            
        Returns:
            tuple: (can_join: bool, reason: str)
        """
        # Check if already a member
        from app.models.community_member import CommunityMember
        existing = CommunityMember.query.filter_by(
            user_id=user.id,
            community_id=self.community_id
        ).first()
        
        if existing:
            return False, "Already a member"
        
        # Check if community is full
        if self.is_full():
            return False, "Community is full"
        
        # Check if community is active
        if not self.is_active:
            return False, "Community is not active"
        
        if self.is_archived:
            return False, "Community is archived"
        
        # Check college restriction
        if self.is_college_specific and user.college_id != self.college_id:
            return False, "This community is only for students from a specific college"
        
        return True, "Can join"
    
    def increment_member_count(self):
        """Increment member count (called when user joins)"""
        self.current_member_count += 1
    
    def decrement_member_count(self):
        """Decrement member count (called when user leaves)"""
        if self.current_member_count > 0:
            self.current_member_count -= 1