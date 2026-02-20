from app.extensions import db
from datetime import datetime, timezone


class TaskCompletion(db.Model):
    """
    Tracks individual user progress on community tasks.
    Each user can complete actions independently.
    """
    __tablename__ = "task_completions"

    id = db.Column(db.Integer, primary_key=True)
    
    task_id = db.Column(
        db.Integer,
        db.ForeignKey("community_tasks.task_id"),
        nullable=False
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Array of completed action IDs: [1, 2, 3]
    completed_actions = db.Column(db.JSON, default=list, nullable=False)
    
    # Completion percentage (0.0 - 100.0)
    completion_percentage = db.Column(db.Float, default=0.0, nullable=False)
    
    # XP awarded so far
    xp_awarded = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_action_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)  # Set when 100% complete

    # ===== Relationships =====
    task = db.relationship("CommunityTask", backref="completions")
    user = db.relationship("User", backref="task_completions")
    
    # Composite unique constraint: one completion record per user per task
    __table_args__ = (
        db.UniqueConstraint('user_id', 'task_id', name='uix_user_task_completion'),
    )
    
    def __repr__(self):
        return f"<TaskCompletion user={self.user_id} task={self.task_id} {self.completion_percentage}%>"
    
    def mark_action_complete(self, action_id, action_xp):
        """
        Mark a specific action as complete and award XP.
        
        Args:
            action_id: Integer action ID
            action_xp: XP to award for this action
            
        Returns:
            Boolean: True if action was newly completed, False if already done
        """
        # Initialize if None
        if self.completed_actions is None:
            self.completed_actions = []
        
        # A task with no defined actions cannot be marked as complete
        if not self.task.actions:
            return False
        
        # Check if already completed
        if action_id in self.completed_actions:
            return False
        
        # Mark as complete
        if action_xp < 0:
            raise ValueError(f"action_xp must be non-negative, got {action_xp}")
        self.completed_actions = self.completed_actions + [action_id]
        self.xp_awarded += action_xp
        self.last_action_at = datetime.now(timezone.utc)
        
        # Update completion percentage
        total_actions = len(self.task.actions)
        self.completion_percentage = (len(self.completed_actions) / total_actions) * 100.0
        
        # Mark as fully completed if 100%
        if self.completion_percentage >= 100.0 and not self.completed_at:
            self.completed_at = datetime.now(timezone.utc)
        
        return True
    
    def unmark_action(self, action_id, action_xp):
        """
        Unmark an action (in case of mistake).
        
        Args:
            action_id: Integer action ID
            action_xp: XP to deduct
            
        Returns:
            Boolean: True if action was unmarked, False if not found
        """
        if not self.completed_actions or action_id not in self.completed_actions:
            return False
        
        updated = list(self.completed_actions)
        updated.remove(action_id)
        self.completed_actions = updated
        self.xp_awarded = max(0, self.xp_awarded - action_xp)
        self.last_action_at = datetime.now(timezone.utc)
        
        # Update completion percentage
        total_actions = len(self.task.actions) if self.task.actions else 0
        self.completion_percentage = (
            (len(self.completed_actions) / total_actions) * 100.0
            if total_actions > 0 else 0.0
        )
        
        # Clear completed_at if no longer 100%
        if self.completion_percentage < 100.0:
            self.completed_at = None
        
        return True
    
    def is_action_completed(self, action_id):
        """Check if a specific action is completed"""
        return action_id in (self.completed_actions or [])
    
    def get_next_incomplete_action(self):
        """
        Get the next incomplete action.
        
        Returns:
            Dict of action or None
        """
        if not self.task.actions:
            return None
        
        completed = self.completed_actions or []
        
        for action in self.task.actions:
            if action.get('id') not in completed:
                return action
        
        return None
