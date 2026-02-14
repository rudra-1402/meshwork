from app.extensions import db
from datetime import datetime


class CommunityTask(db.Model):
    """
    Tasks created by admins/moderators for community members.
    Each task has multiple actions (sub-tasks) that users can complete individually.
    """
    __tablename__ = "community_tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    
    community_id = db.Column(
        db.Integer,
        db.ForeignKey("communities.community_id"),
        nullable=False
    )
    
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Task details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Difficulty level: "Easy", "Medium", "Hard"
    difficulty = db.Column(db.String(20), nullable=False, default="Medium")
    
    # XP reward (max XP user can earn from this task)
    # Each action completion gives: max_xp / number_of_actions
    max_xp_reward = db.Column(db.Integer, default=0, nullable=False)
    
    # Deadline (optional)
    deadline = db.Column(db.DateTime, nullable=True)
    
    # Actions (sub-tasks) stored as JSON array
    # Example: [
    #   {"id": 1, "text": "Set up environment", "xp": 10},
    #   {"id": 2, "text": "Complete module 1", "xp": 15},
    #   {"id": 3, "text": "Write tests", "xp": 25}
    # ]
    # Note: Individual action XP calculated based on admin weighting
    actions = db.Column(db.JSON, nullable=False)
    
    # Task status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ===== Relationships =====
    community = db.relationship("Community", backref="tasks")
    creator = db.relationship("User", backref="created_tasks")
    
    def __repr__(self):
        return f"<CommunityTask '{self.title}' in community={self.community_id}>"
    
    def get_total_actions(self):
        """Get total number of actions in this task"""
        if not self.actions:
            return 0
        return len(self.actions)
    
    def get_action_by_id(self, action_id):
        """
        Get a specific action by ID.
        
        Args:
            action_id: Integer action ID
            
        Returns:
            Dict of action or None
        """
        if not self.actions:
            return None
        
        for action in self.actions:
            if action.get('id') == action_id:
                return action
        return None
    
    def calculate_xp_for_actions(self, completed_action_ids):
        """
        Calculate total XP earned from completing specific actions.
        
        Args:
            completed_action_ids: List of action IDs completed
            
        Returns:
            Integer XP amount
        """
        if not self.actions or not completed_action_ids:
            return 0
        
        total_xp = 0
        for action in self.actions:
            if action.get('id') in completed_action_ids:
                total_xp += action.get('xp', 0)
        
        return total_xp
    
    def get_completion_stats(self):
        """
        Get statistics about how many users completed this task.
        
        Returns:
            Dict with completion stats
        """
        from app.models.task_completion import TaskCompletion
        
        completions = TaskCompletion.query.filter_by(task_id=self.task_id).all()
        
        if not completions:
            return {
                "total_users": 0,
                "completed_all": 0,
                "average_completion": 0.0
            }
        
        total_users = len(completions)
        completed_all = sum(1 for c in completions if c.completion_percentage >= 100.0)
        avg_completion = sum(c.completion_percentage for c in completions) / total_users
        
        return {
            "total_users": total_users,
            "completed_all": completed_all,
            "average_completion": round(avg_completion, 1)
        }
