"""
XP Service

All XP awarding logic, daily cap enforcement, and diminishing returns.
This is the ONLY place where XP should be awarded or removed.
"""

from app.extensions import db
from app.models.xp_transaction import XPTransaction
from app.constants.gamification import (
    DAILY_XP_CAP,
    XP_AMOUNTS,
    ACTION_DAILY_LIMITS,
    DIMINISHING_RETURNS_STAGES,
)
from datetime import date, datetime
from sqlalchemy import func


class XPService:
    """
    Centralized XP management service.
    
    All XP awards MUST go through this service to ensure:
    - Daily cap enforcement
    - Diminishing returns
    - Audit trail (XPTransaction)
    - Level-up detection
    """
    
    @staticmethod
    def award_xp(user, amount, source, description="", 
                 related_entity_type=None, related_entity_id=None,
                 bypass_cap=False):
        """
        Award XP to a user with all business rules enforced.
        
        Args:
            user: User instance
            amount: XP amount to award (positive integer)
            source: String describing source (e.g., 'challenge', 'daily_login')
            description: Optional detailed description
            related_entity_type: Optional entity type ('Challenge', 'Project', etc.)
            related_entity_id: Optional entity ID
            bypass_cap: If True, skip daily cap check (admin bonuses only)
            
        Returns:
            dict: {
                'success': bool,
                'xp_awarded': int,
                'xp_requested': int,
                'leveled_up': bool,
                'old_level': int,
                'new_level': int,
                'daily_xp_remaining': int,
                'reason': str (if partial/denied)
            }
        """
        # Validate amount
        if amount <= 0:
            return {
                'success': False,
                'xp_awarded': 0,
                'xp_requested': amount,
                'reason': 'XP amount must be positive'
            }
        
        # Reset daily counter if needed
        XPService._reset_daily_xp_if_needed(user)
        
        # Apply diminishing returns
        if not bypass_cap:
            amount = XPService._apply_diminishing_returns(user, amount, source)
        
        # Check daily cap
        if not bypass_cap:
            can_earn, actual_amount, cap_reason = XPService._check_daily_cap(user, amount)
            
            if not can_earn:
                return {
                    'success': False,
                    'xp_awarded': 0,
                    'xp_requested': amount,
                    'reason': cap_reason,
                    'daily_xp_remaining': 0
                }
        else:
            actual_amount = amount
            cap_reason = None
        
        # Record balance before
        balance_before = user.xp
        
        # Update user XP
        user.xp += actual_amount
        if not bypass_cap:
            user.daily_xp_earned += actual_amount
        
        # Check for level-up
        leveled_up, old_level, new_level = user.update_level()
        
        # Create audit transaction
        transaction = XPTransaction.log_transaction(
            user_id=user.id,
            amount=actual_amount,
            source=source,
            description=description,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            balance_before=balance_before,
            balance_after=user.xp,
            metadata={
                'daily_xp_earned': user.daily_xp_earned,
                'leveled_up': leveled_up,
                'bypass_cap': bypass_cap
            }
        )
        db.session.add(transaction)
        
        # Commit transaction
        db.session.commit()
        
        return {
            'success': True,
            'xp_awarded': actual_amount,
            'xp_requested': amount,
            'leveled_up': leveled_up,
            'old_level': old_level,
            'new_level': new_level,
            'daily_xp_remaining': max(0, DAILY_XP_CAP - user.daily_xp_earned),
            'reason': cap_reason if actual_amount < amount else None
        }
    
    @staticmethod
    def remove_xp(user, amount, reason, related_entity_type=None, related_entity_id=None):
        """
        Remove XP from user (for penalties, violations, etc.).
        
        Args:
            user: User instance
            amount: XP amount to remove (positive integer)
            reason: String describing reason for penalty
            related_entity_type: Optional entity type
            related_entity_id: Optional entity ID
            
        Returns:
            dict: {
                'success': bool,
                'xp_removed': int,
                'new_xp': int,
                'new_level': int,
                'level_dropped': bool
            }
        """
        if amount <= 0:
            return {
                'success': False,
                'xp_removed': 0,
                'reason': 'Amount must be positive'
            }
        
        balance_before = user.xp
        old_level = user.level
        
        # Remove XP (cannot go below 0)
        user.xp = max(0, user.xp - amount)
        
        # Recalculate level
        leveled_up, _, new_level = user.update_level()
        level_dropped = new_level < old_level
        
        # Create audit transaction (NEGATIVE amount)
        transaction = XPTransaction.log_transaction(
            user_id=user.id,
            amount=-amount,  # NEGATIVE
            source='penalty',
            description=reason,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            balance_before=balance_before,
            balance_after=user.xp,
            metadata={
                'penalty_type': 'xp_removal',
                'level_dropped': level_dropped
            }
        )
        db.session.add(transaction)
        
        # Commit
        db.session.commit()
        
        return {
            'success': True,
            'xp_removed': amount,
            'new_xp': user.xp,
            'old_level': old_level,
            'new_level': new_level,
            'level_dropped': level_dropped
        }
    
    @staticmethod
    def award_standard_xp(user, action_type, **kwargs):
        """
        Award XP using standard amounts from constants.
        
        Args:
            user: User instance
            action_type: Key from XP_AMOUNTS (e.g., 'daily_login')
            **kwargs: Additional args for award_xp()
            
        Returns:
            dict: Result from award_xp()
        """
        amount = XP_AMOUNTS.get(action_type, 0)
        
        if amount == 0:
            return {
                'success': False,
                'xp_awarded': 0,
                'reason': f'Unknown action type: {action_type}'
            }
        
        return XPService.award_xp(
            user=user,
            amount=amount,
            source=action_type,
            description=kwargs.get('description', f'XP for {action_type}'),
            related_entity_type=kwargs.get('related_entity_type'),
            related_entity_id=kwargs.get('related_entity_id'),
            bypass_cap=kwargs.get('bypass_cap', False)
        )
    
    @staticmethod
    def _reset_daily_xp_if_needed(user):
        """
        Reset daily XP counter if it's a new day.
        
        Args:
            user: User instance (modified in place)
        """
        today = date.today()
        
        if user.last_xp_reset_date != today:
            user.daily_xp_earned = 0
            user.last_xp_reset_date = today
    
    @staticmethod
    def _check_daily_cap(user, amount):
        """
        Check if user can earn XP without exceeding daily cap.
        
        Args:
            user: User instance
            amount: XP amount requested
            
        Returns:
            tuple: (can_earn: bool, actual_amount: int, reason: str)
        """
        remaining = DAILY_XP_CAP - user.daily_xp_earned
        
        if remaining <= 0:
            return False, 0, f"Daily XP cap ({DAILY_XP_CAP} XP) reached"
        
        if amount <= remaining:
            return True, amount, "Can earn full amount"
        
        # Partial XP
        return True, remaining, f"Can only earn {remaining} XP (daily cap)"
    
    @staticmethod
    def _apply_diminishing_returns(user, amount, source):
        """
        Apply diminishing returns after repeated actions.
        
        Args:
            user: User instance
            amount: Original XP amount
            source: Action source
            
        Returns:
            int: Adjusted XP amount
        """
        # Check if this action type has a limit
        limit = ACTION_DAILY_LIMITS.get(source)
        
        if limit is None:
            # No diminishing returns for this action
            return amount
        
        # Count how many times this action was performed today
        today = date.today()
        
        count_today = (
            XPTransaction.query
            .filter_by(user_id=user.id, source=source)
            .filter(func.date(XPTransaction.created_at) == today)
            .count()
        )
        
        # Apply multiplier based on count
        if count_today < limit:
            # Below limit - full XP
            multiplier = DIMINISHING_RETURNS_STAGES[0][0]
        elif count_today < limit * 2:
            # 1-2x limit - 50% XP
            multiplier = DIMINISHING_RETURNS_STAGES[1][0]
        else:
            # 2x+ limit - 10% XP
            multiplier = DIMINISHING_RETURNS_STAGES[2][0]
        
        adjusted_amount = int(amount * multiplier)
        
        return adjusted_amount
    
    @staticmethod
    def get_daily_summary(user):
        """
        Get user's XP summary for today.
        
        Args:
            user: User instance
            
        Returns:
            dict: {
                'daily_xp_earned': int,
                'daily_xp_remaining': int,
                'transactions_today': list,
                'breakdown_by_source': dict
            }
        """
        today = date.today()
        
        transactions = (
            XPTransaction.query
            .filter_by(user_id=user.id)
            .filter(func.date(XPTransaction.created_at) == today)
            .order_by(XPTransaction.created_at.desc())
            .all()
        )
        
        # Breakdown by source
        breakdown = {}
        for t in transactions:
            breakdown[t.source] = breakdown.get(t.source, 0) + t.amount
        
        return {
            'daily_xp_earned': user.daily_xp_earned,
            'daily_xp_remaining': max(0, DAILY_XP_CAP - user.daily_xp_earned),
            'daily_cap': DAILY_XP_CAP,
            'transaction_count': len(transactions),
            'breakdown_by_source': breakdown,
            'transactions': [
                {
                    'amount': t.amount,
                    'source': t.source,
                    'description': t.description,
                    'created_at': t.created_at.isoformat()
                }
                for t in transactions
            ]
        }
    
    @staticmethod
    def get_xp_leaderboard(limit=10):
        """
        Get top users by XP.
        
        Args:
            limit: Number of users to return
            
        Returns:
            list: Top users with XP and level
        """
        from app.models.user_gamified import User
        
        top_users = (
            User.query
            .order_by(User.xp.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                'user_id': u.id,
                'username': u.username,
                'xp': u.xp,
                'level': u.level,
                'reputation': u.reputation
            }
            for u in top_users
        ]