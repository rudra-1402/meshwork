from app.extensions import db
from datetime import datetime, timezone


class XPTransaction(db.Model):
    """
    Complete audit log of all XP transactions.
    Every XP gain/loss is recorded for transparency and debugging.
    """
    __tablename__ = "xp_transactions"

    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    
    # XP amount (positive for gains, negative for penalties)
    amount = db.Column(db.Integer, nullable=False)
    
    # Source of XP
    source = db.Column(db.String(50), nullable=False)
    # Values: "login", "streak_bonus", "challenge", "project", "event", 
    #         "community_join", "task", "admin_adjustment", etc.
    
    # Detailed description
    description = db.Column(db.Text, nullable=True)
    
    # Related entity (optional)
    related_entity_type = db.Column(db.String(50), nullable=True)  # "challenge", "project", "event"
    related_entity_id = db.Column(db.Integer, nullable=True)
    
    # Balance tracking
    balance_before = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Metadata (JSON for additional context)
    extra_data = db.Column(db.JSON, nullable=True)

    # ===== Relationships =====
    user = db.relationship("User", backref="xp_transactions")
    
    # Index for efficient queries
    __table_args__ = (
        db.Index('idx_xp_transactions_user_created', 'user_id', 'created_at'),
        db.Index('idx_source', 'source'),
    )
    
    def __repr__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"<XPTransaction user={self.user_id} {sign}{self.amount} XP from {self.source}>"
    
    @staticmethod
    def log_transaction(user_id, amount, source, description="", 
                       related_entity_type=None, related_entity_id=None,
                       balance_before=0, balance_after=0, metadata=None):
        """
        Create and return a transaction log entry (not committed).
        
        Args:
            user_id: User ID
            amount: XP amount
            source: Source string
            description: Optional description
            related_entity_type: Optional entity type
            related_entity_id: Optional entity ID
            balance_before: XP before transaction
            balance_after: XP after transaction
            metadata: Optional JSON metadata
            
        Returns:
            XPTransaction instance (not committed)
        """
        return XPTransaction(
            user_id=user_id,
            amount=amount,
            source=source,
            description=description,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            balance_before=balance_before,
            balance_after=balance_after,
            extra_data=metadata
        )
    
    @staticmethod
    def get_user_history(user_id, limit=50, source_filter=None):
        """
        Get user's XP transaction history.
        
        Args:
            user_id: User ID
            limit: Max number of entries
            source_filter: Optional source filter (e.g., "challenge")
            
        Returns:
            List of XPTransaction instances
        """
        query = XPTransaction.query.filter_by(user_id=user_id)
        
        if source_filter:
            query = query.filter_by(source=source_filter)
        
        return query.order_by(XPTransaction.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_daily_summary(user_id, date_obj):
        """
        Get XP summary for a specific day.
        
        Args:
            user_id: User ID
            date_obj: Date object
            
        Returns:
            Dict with total_xp, transactions, breakdown_by_source
        """
        from datetime import datetime, timedelta, timezone
        
        # Start and end of day — must be tz-aware to match the UTC-aware created_at column
        start = datetime.combine(date_obj, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        
        transactions = (
            XPTransaction.query
            .filter(
                XPTransaction.user_id == user_id,
                XPTransaction.created_at >= start,
                XPTransaction.created_at < end
            )
            .all()
        )
        
        total_xp = sum(t.amount for t in transactions)
        
        # Breakdown by source
        breakdown = {}
        for t in transactions:
            breakdown[t.source] = breakdown.get(t.source, 0) + t.amount
        
        return {
            "date": date_obj.isoformat(),
            "total_xp": total_xp,
            "transaction_count": len(transactions),
            "breakdown": breakdown,
            "transactions": transactions
        }
