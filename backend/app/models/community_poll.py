from app.extensions import db
from datetime import datetime


class CommunityPoll(db.Model):
    """
    Polls created in communities for voting.
    """
    __tablename__ = "community_polls"

    poll_id = db.Column(db.Integer, primary_key=True)
    
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
    
    question = db.Column(db.String(300), nullable=False)
    
    # Poll options stored as JSON
    # Example: [{"id": 1, "text": "Option A", "votes": 0}, ...]
    options = db.Column(db.JSON, nullable=False)
    
    # Allow multiple selections?
    allow_multiple = db.Column(db.Boolean, default=False)
    
    # Anonymous voting?
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Deadline
    expires_at = db.Column(db.DateTime, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ===== Relationships =====
    community = db.relationship("Community", backref="polls")
    creator = db.relationship("User", backref="created_polls")
    
    def __repr__(self):
        return f"<CommunityPoll '{self.question[:30]}...'>"


class PollVote(db.Model):
    """
    Individual votes on polls.
    """
    __tablename__ = "poll_votes"

    id = db.Column(db.Integer, primary_key=True)
    
    poll_id = db.Column(
        db.Integer,
        db.ForeignKey("community_polls.poll_id"),
        nullable=False
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # Array of selected option IDs: [1, 3] (if multiple allowed)
    selected_options = db.Column(db.JSON, nullable=False)
    
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ===== Relationships =====
    poll = db.relationship("CommunityPoll", backref="votes")
    user = db.relationship("User", backref="poll_votes")
    
    # Unique constraint: one vote per user per poll
    __table_args__ = (
        db.UniqueConstraint('user_id', 'poll_id', name='uix_user_poll_vote'),
    )
