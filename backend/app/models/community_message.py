from app.extensions import db
from datetime import datetime


class CommunityMessage(db.Model):
    """
    Messages in community chat.
    Supports different types: regular messages, announcements, tasks, polls, files.
    """
    __tablename__ = "community_messages"

    message_id = db.Column(db.Integer, primary_key=True)

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

    # Message content
    message = db.Column(db.Text, nullable=False)
    
    # Message type: "message", "announcement", "task", "poll", "file", "event"
    message_type = db.Column(db.String(20), default="message", nullable=False)
    
    # Related entities (nullable, only used when message_type != "message")
    related_task_id = db.Column(
        db.Integer,
        db.ForeignKey("community_tasks.task_id"),
        nullable=True
    )
    
    related_poll_id = db.Column(db.Integer, nullable=True)  # Future: CommunityPoll
    related_file_id = db.Column(db.Integer, nullable=True)  # Future: CommunityFile
    related_event_id = db.Column(db.Integer, nullable=True) # Future: Event
    
    # Message features
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata (JSON for flexibility)
    # Can store: {"edited": true, "reactions": {"👍": 5}, ...}
    meta_data = db.Column(db.JSON, nullable=True)

    # Timestamps
    messaged_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    edited_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # ===== Relationships =====
    sender = db.relationship("User", backref="community_messages")
    community = db.relationship("Community", backref="messages")
    related_task = db.relationship("CommunityTask", backref="task_messages")
    
    def __repr__(self):
        return f"<CommunityMessage {self.message_type} in community={self.community_id}>"
    
    def is_announcement(self):
        """Check if this is an announcement"""
        return self.message_type == "announcement"
    
    def is_task_message(self):
        """Check if this message is linked to a task"""
        return self.message_type == "task" and self.related_task_id is not None
    
    def soft_delete(self):
        """Soft delete message (mark as deleted but keep in database)"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def pin(self):
        """Pin this message"""
        self.is_pinned = True
    
    def unpin(self):
        """Unpin this message"""
        self.is_pinned = False
    
    def edit(self, new_content):
        """
        Edit message content.
        
        Args:
            new_content: New message text
        """
        self.message = new_content
        self.edited_at = datetime.utcnow()
        
        # Update metadata to mark as edited
        if not self.metadata:
            self.metadata = {}
        self.metadata['edited'] = True
    
    @staticmethod
    def create_task_announcement(community_id, user_id, task):
        """
        Create a message announcing a new task.
        
        Args:
            community_id: Community ID
            user_id: Creator user ID
            task: CommunityTask instance
            
        Returns:
            CommunityMessage instance (not committed)
        """
        message_text = (
            f"📋 **New Task:** {task.title}\n\n"
            f"{task.description or 'No description provided.'}\n\n"
            f"**Difficulty:** {task.difficulty}\n"
            f"**Max XP Reward:** {task.max_xp_reward} XP\n"
            f"**Actions:** {len(task.actions) if task.actions else 0}"
        )
        
        if task.deadline:
            message_text += f"\n**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}"
        
        return CommunityMessage(
            user_id=user_id,
            community_id=community_id,
            message=message_text,
            message_type="task",
            related_task_id=task.task_id,
            is_pinned=True  # Pin task announcements by default
        )