from app.extensions import db
from datetime import datetime, timezone


class CommunityModerator(db.Model):
    """
    Moderators are community members with elevated permissions.
    Promoted by admin, can create events, manage tasks, moderate messages.
    """
    __tablename__ = "community_moderators"

    id = db.Column(db.Integer, primary_key=True)
    
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
    
    # Who promoted this user to moderator
    promoted_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Moderator permissions (JSON for flexibility)
    # Example: {"can_create_tasks": true, "can_delete_messages": false, ...}
    permissions = db.Column(db.JSON, nullable=True)
    
    promoted_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ===== Relationships =====
    user = db.relationship("User", foreign_keys=[user_id], backref="moderator_roles")
    community = db.relationship("Community", backref="moderators")
    promoter = db.relationship("User", foreign_keys=[promoted_by])
    
    # Composite unique constraint: one moderator role per user per community
    __table_args__ = (
        db.UniqueConstraint('user_id', 'community_id', name='uix_user_community_moderator'),
        db.Index('idx_community_moderators_user_id', 'user_id'),
        db.Index('idx_community_moderators_community_id', 'community_id'),
    )
    
    def __repr__(self):
        return f"<CommunityModerator user_id={self.user_id} community_id={self.community_id}>"
    
    @staticmethod
    def get_default_permissions():
        """Default permissions for new moderators"""
        return {
            "can_create_tasks": True,
            "can_create_events": True,
            "can_send_announcements": True,
            "can_create_polls": True,
            "can_delete_messages": False,  # Only admin by default
            "can_remove_members": False,   # Only admin by default
            "can_pin_messages": True,
            "can_manage_files": True
        }
    
    def has_permission(self, permission_name):
        """
        Check if moderator has a specific permission.
        
        Args:
            permission_name: String like "can_create_tasks"
            
        Returns:
            Boolean
        """
        if not self.is_active:
            return False
        
        if not self.permissions:
            self.permissions = self.get_default_permissions()
        
        return self.permissions.get(permission_name, False)
