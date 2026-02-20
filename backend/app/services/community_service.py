from app.extensions import db
from app.models.community import Community
from app.models.community_member import CommunityMember
from app.models.community_moderator import CommunityModerator
from app.models.community_task import CommunityTask
from app.models.task_completion import TaskCompletion
from app.models.community_message import CommunityMessage
from app.models.user import User
from app.services.xp_service import XPService
import logging

logger = logging.getLogger(__name__)


class CommunityService:
    """
    Service layer for all community-related operations.
    Handles creation, settings, tasks, moderators, and permissions.
    """
    
    # ===== COMMUNITY CREATION & MANAGEMENT =====
    
    @staticmethod
    def create_community(
        community_name,
        subject,
        college_id,
        user_id,
        description=None,
        max_members=50,
        is_college_specific=True,
        programming_languages=None
    ):
        """
        Create a new community with settings.
        
        Args:
            community_name: String
            subject: String
            college_id: Integer
            user_id: Integer (creator)
            description: Optional string
            max_members: Integer (default: 50)
            is_college_specific: Boolean (default: True)
            programming_languages: List of strings (e.g., ["Python", "Java"])
            
        Returns:
            Community instance
        """
        # Create community
        community = Community(
            community_name=community_name,
            subject=subject,
            college_id=college_id,
            created_by=user_id,
            description=description,
            max_members=max_members,
            current_member_count=1,  # Creator is first member
            is_college_specific=is_college_specific,
            programming_languages=programming_languages or [],
            is_active=True
        )
        
        db.session.add(community)
        db.session.flush()  # Get community_id before commit
        
        # Add creator as first member
        member = CommunityMember(
            user_id=user_id,
            community_id=community.community_id
        )
        
        db.session.add(member)
        db.session.commit()
        
        logger.info(f"Created community '{community_name}' (ID: {community.community_id}) by user {user_id}")
        
        return community
    
    @staticmethod
    def update_community_settings(community_id, user_id, **kwargs):
        """
        Update community settings.
        Only admin can update. Certain changes require confirmation.
        
        Args:
            community_id: Integer
            user_id: Integer (must be admin)
            **kwargs: Settings to update
            
        Returns:
            tuple: (success: bool, message: str, community: Community or None)
        """
        community = db.session.get(Community, community_id)
        
        if not community:
            return False, "Community not found", None
        
        # Check if user is admin
        if community.created_by != user_id:
            return False, "Only the community admin can update settings", None
        
        # Update allowed fields
        allowed_fields = [
            'community_name', 'subject', 'description', 'max_members',
            'is_college_specific', 'programming_languages', 'is_active'
        ]
        
        critical_fields = ['is_college_specific']  # Require confirmation
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                # Check if this is a critical field change
                if field in critical_fields:
                    current_value = getattr(community, field)
                    if current_value != value:
                        # Log critical change
                        logger.warning(
                            f"Critical setting change for community {community_id}: "
                            f"{field} changed from {current_value} to {value}"
                        )
                
                setattr(community, field, value)
        
        db.session.commit()
        
        logger.info(f"Updated settings for community {community_id} by user {user_id}")
        
        return True, "Settings updated successfully", community
    
    # ===== MODERATOR MANAGEMENT =====
    
    @staticmethod
    def promote_to_moderator(community_id, admin_id, user_id, permissions=None):
        """
        Promote a user to moderator.
        
        Args:
            community_id: Integer
            admin_id: Integer (must be admin)
            user_id: Integer (user to promote)
            permissions: Optional dict of permissions
            
        Returns:
            tuple: (success: bool, message: str)
        """
        community = db.session.get(Community, community_id)
        
        if not community:
            return False, "Community not found"
        
        # Check if requester is admin
        if community.created_by != admin_id:
            return False, "Only the admin can promote moderators"
        
        # Check if user is a member
        member = CommunityMember.query.filter_by(
            user_id=user_id,
            community_id=community_id
        ).first()
        
        if not member:
            return False, "User must be a member to become a moderator"
        
        # Check if already a moderator
        existing_mod = CommunityModerator.query.filter_by(
            user_id=user_id,
            community_id=community_id
        ).first()
        
        if existing_mod:
            return False, "User is already a moderator"
        
        # Create moderator role
        moderator = CommunityModerator(
            user_id=user_id,
            community_id=community_id,
            promoted_by=admin_id,
            permissions=permissions or CommunityModerator.get_default_permissions()
        )
        
        db.session.add(moderator)
        db.session.commit()
        
        logger.info(f"User {user_id} promoted to moderator in community {community_id} by {admin_id}")
        
        return True, "User promoted to moderator successfully"
    
    @staticmethod
    def remove_moderator(community_id, admin_id, user_id):
        """
        Remove moderator status from a user.
        
        Args:
            community_id: Integer
            admin_id: Integer (must be admin)
            user_id: Integer (moderator to remove)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        community = db.session.get(Community, community_id)
        
        if not community or community.created_by != admin_id:
            return False, "Only the admin can remove moderators"
        
        moderator = CommunityModerator.query.filter_by(
            user_id=user_id,
            community_id=community_id
        ).first()
        
        if not moderator:
            return False, "User is not a moderator"
        
        db.session.delete(moderator)
        db.session.commit()
        
        logger.info(f"Removed moderator {user_id} from community {community_id}")
        
        return True, "Moderator removed successfully"
    
    @staticmethod
    def is_admin(community_id, user_id):
        """Check if user is admin of community"""
        community = db.session.get(Community, community_id)
        return community and community.created_by == user_id
    
    @staticmethod
    def is_moderator(community_id, user_id):
        """Check if user is moderator of community"""
        moderator = CommunityModerator.query.filter_by(
            user_id=user_id,
            community_id=community_id,
            is_active=True
        ).first()
        return moderator is not None
    
    @staticmethod
    def can_user_perform_action(community_id, user_id, action):
        """
        Check if user can perform a specific action.
        
        Args:
            community_id: Integer
            user_id: Integer
            action: String like "create_tasks", "delete_messages", etc.
            
        Returns:
            Boolean
        """
        # Admin can do everything
        if CommunityService.is_admin(community_id, user_id):
            return True
        
        # Check moderator permissions
        moderator = CommunityModerator.query.filter_by(
            user_id=user_id,
            community_id=community_id,
            is_active=True
        ).first()
        
        if moderator:
            return moderator.has_permission(f"can_{action}")
        
        return False
    
    # ===== TASK MANAGEMENT =====
    
    @staticmethod
    def create_task(
        community_id,
        user_id,
        title,
        description,
        actions,
        difficulty="Medium",
        max_xp_reward=0,
        deadline=None
    ):
        """
        Create a new task in the community.
        
        Args:
            community_id: Integer
            user_id: Integer (admin or moderator)
            title: String
            description: String
            actions: List of dicts like [{"id": 1, "text": "Do X", "xp": 10}, ...]
            difficulty: String ("Easy", "Medium", "Hard")
            max_xp_reward: Integer
            deadline: Optional datetime
            
        Returns:
            tuple: (success: bool, message: str, task: CommunityTask or None)
        """
        # Check permissions
        if not CommunityService.can_user_perform_action(community_id, user_id, "create_tasks"):
            return False, "You don't have permission to create tasks", None
        
        # Validate actions
        if not actions or not isinstance(actions, list):
            return False, "Task must have at least one action", None
        
        # Create task
        task = CommunityTask(
            community_id=community_id,
            created_by=user_id,
            title=title,
            description=description,
            difficulty=difficulty,
            max_xp_reward=max_xp_reward,
            deadline=deadline,
            actions=actions,
            is_active=True
        )
        
        db.session.add(task)
        db.session.flush()
        
        # Create announcement message
        task_message = CommunityMessage.create_task_announcement(
            community_id=community_id,
            user_id=user_id,
            task=task
        )
        
        db.session.add(task_message)
        db.session.commit()
        
        logger.info(f"Created task '{title}' in community {community_id} by user {user_id}")
        
        return True, "Task created successfully", task
    
    @staticmethod
    def mark_action_complete(task_id, user_id, action_id):
        """
        Mark a task action as complete for a user.
        
        Args:
            task_id: Integer
            user_id: Integer
            action_id: Integer (action ID from task.actions)
            
        Returns:
            tuple: (success: bool, message: str, xp_awarded: int)
        """
        task = db.session.get(CommunityTask, task_id)
        
        if not task or not task.is_active:
            return False, "Task not found or inactive", 0
        
        # Get or create completion record
        completion = TaskCompletion.query.filter_by(
            task_id=task_id,
            user_id=user_id
        ).first()
        
        if not completion:
            completion = TaskCompletion(
                task_id=task_id,
                user_id=user_id,
                completed_actions=[],
                completion_percentage=0.0,
                xp_awarded=0
            )
            db.session.add(completion)
        
        # Get action XP
        action = task.get_action_by_id(action_id)
        if not action:
            return False, "Action not found", 0
        
        action_xp = action.get('xp', 0)
        
        # Mark action complete
        was_new = completion.mark_action_complete(action_id, action_xp)
        
        if not was_new:
            return False, "Action already completed", 0
        
        # Award XP to user via XPService (enforces daily cap, diminishing returns, audit trail)
        user = db.session.get(User, user_id)
        if user and action_xp > 0:
            XPService.award_xp(
                user=user,
                amount=action_xp,
                source='task_complete',
                description='Community task action completed'
            )
        else:
            db.session.commit()
        
        logger.info(
            f"User {user_id} completed action {action_id} of task {task_id}, "
            f"awarded {action_xp} XP"
        )
        
        return True, f"Action completed! +{action_xp} XP", action_xp
    
    @staticmethod
    def get_task_completions(task_id):
        """
        Get all user completions for a task.
        
        Args:
            task_id: Integer
            
        Returns:
            List of TaskCompletion instances
        """
        return TaskCompletion.query.filter_by(task_id=task_id).all()
    
    @staticmethod
    def get_user_task_progress(task_id, user_id):
        """
        Get user's progress on a specific task.
        
        Args:
            task_id: Integer
            user_id: Integer
            
        Returns:
            TaskCompletion instance or None
        """
        return TaskCompletion.query.filter_by(
            task_id=task_id,
            user_id=user_id
        ).first()


    # ===== JOIN COMMUNITY =====

    @staticmethod
    def join_community(community_id, user_id):
        """
        Add a user as a member of a community.

        Prevents duplicate membership silently (idempotent).

        Args:
            community_id: Integer
            user_id: Integer

        Returns:
            tuple: (joined: bool, message: str)
        """
        community = db.session.get(Community, community_id)
        if not community:
            return False, "Community not found"

        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"

        can_join, reason = CommunityService.can_user_join(community, user)
        if not can_join:
            return False, reason

        member = CommunityMember(
            user_id=user_id,
            community_id=community_id
        )
        db.session.add(member)
        community.increment_member_count()
        db.session.commit()

        logger.info(f"User {user_id} joined community {community_id}")

        return True, "Joined community successfully"

    # ===== SEND MESSAGE =====

    @staticmethod
    def send_message(community_id, user_id, message_text):
        """
        Persist a new message in a community.

        Caller is responsible for verifying the user is the community admin
        before calling this method.

        Args:
            community_id: Integer
            user_id: Integer (sender)
            message_text: String (non-empty, pre-validated by caller)

        Returns:
            tuple: (success: bool, message: str, msg_obj: CommunityMessage or None)
        """
        try:
            msg = CommunityMessage(
                user_id=user_id,
                community_id=community_id,
                message=message_text
            )
            db.session.add(msg)
            db.session.commit()

            logger.info(f"User {user_id} sent message in community {community_id}")

            return True, "Message sent successfully", msg

        except Exception as exc:
            db.session.rollback()
            logger.error(f"Failed to send message in community {community_id}: {exc}")
            return False, "Failed to send message", None

    # ===== MEMBERSHIP ELIGIBILITY =====

    @staticmethod
    def can_user_join(community, user):
        """
        Check if a user is eligible to join a community.

        Args:
            community: Community instance
            user: User instance

        Returns:
            tuple: (can_join: bool, reason: str)
        """
        existing = CommunityMember.query.filter_by(
            user_id=user.id,
            community_id=community.community_id
        ).first()
        if existing:
            return False, "Already a member"

        if community.current_member_count >= community.max_members:
            return False, "Community is full"

        if not community.is_active:
            return False, "Community is not active"

        if community.is_archived:
            return False, "Community is archived"

        if community.is_college_specific and user.college_id != community.college_id:
            return False, "This community is only for students from a specific college"

        return True, "Can join"

    # ===== TASK STATS =====

    @staticmethod
    def get_task_completion_stats(task_id):
        """
        Get completion statistics for a community task.

        Args:
            task_id: CommunityTask PK

        Returns:
            dict: {total_users, completed_all, average_completion}
        """
        completions = TaskCompletion.query.filter_by(task_id=task_id).all()

        if not completions:
            return {"total_users": 0, "completed_all": 0, "average_completion": 0.0}

        total_users = len(completions)
        completed_all = sum(1 for c in completions if c.completion_percentage >= 100.0)
        avg_completion = sum(c.completion_percentage for c in completions) / total_users

        return {
            "total_users": total_users,
            "completed_all": completed_all,
            "average_completion": round(avg_completion, 1),
        }


# Create singleton instance for easy importing
community_service = CommunityService()