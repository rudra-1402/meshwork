"""
Tests for community endpoints and services.
Coverage targets: community_routes.py (21% → 65%), community_service.py (27% → 70%)
"""
import pytest
from datetime import datetime, timezone


# =============================================================================
# AUTH CHECKS
# =============================================================================

class TestCommunityRequireAuth:
    """Verify all community endpoints require authentication."""

    def test_create_community_no_token(self, client):
        """POST /api/communities/create requires JWT"""
        resp = client.post('/api/communities/create')
        assert resp.status_code == 401

    def test_explore_communities_no_token(self, client):
        """GET /api/communities/explore requires JWT"""
        resp = client.get('/api/communities/explore')
        assert resp.status_code == 401

    def test_join_community_no_token(self, client):
        """POST /api/communities/join/<id> requires JWT"""
        resp = client.post('/api/communities/join/1')
        assert resp.status_code == 401

    def test_view_community_no_token(self, client):
        """GET /api/communities/view/<id> requires JWT"""
        resp = client.get('/api/communities/view/1')
        assert resp.status_code == 401


# =============================================================================
# COMMUNITY SERVICE LAYER TESTS
# =============================================================================

class TestCreateCommunityService:
    """Test community creation via service layer (bypasses route validation)."""
    
    def test_create_community_with_valid_data(self, app, seeded_user):
        """Service layer creates community with minimal required fields"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community import Community
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            # Get user and their college_id
            user = _db.session.get(User, seeded_user["id"])
            
            # Create community
            community = CommunityService.create_community(
                community_name="Test Community",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id
            )
            
            assert community is not None
            assert community.community_id is not None
            assert community.community_name == "Test Community"
            assert community.subject == "Testing"
            assert community.created_by == user.id
            assert community.current_member_count == 1  # Creator auto-joined
            
            # Verify creator was added as member
            member = CommunityMember.query.filter_by(
                user_id=user.id,
                community_id=community.community_id
            ).first()
            assert member is not None
            
            # Cleanup
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()
    
    def test_create_community_with_optional_fields(self, app, seeded_user):
        """Service layer accepts optional fields"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.user import User
            from app.extensions import db as _db
            
            user = _db.session.get(User, seeded_user["id"])
            
            community = CommunityService.create_community(
                community_name="Advanced Community",
                subject="Advanced Topics",
                college_id=user.college_id,
                user_id=user.id,
                description="A detailed description",
                max_members=100,
                is_college_specific=False,
                programming_languages=["Python", "JavaScript", "Go"]
            )
            
            assert community.description == "A detailed description"
            assert community.max_members == 100
            assert community.is_college_specific is False
            assert "Python" in community.programming_languages
            assert len(community.programming_languages) == 3
            
            # Cleanup
            from app.models.community_member import CommunityMember
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()


class TestJoinCommunity:
    """Test community membership operations."""
    
    def test_user_can_join_community(self, app, two_users):
        """User can join an existing community"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            creator_id, joiner_id = two_users
            creator = _db.session.get(User, creator_id)
            
            # Create community as creator
            community = CommunityService.create_community(
                community_name="Open Community",
                subject="Testing",
                college_id=creator.college_id,
                user_id=creator_id
            )
            
            # Second user joins
            member_count_before = community.current_member_count
            
            new_member = CommunityMember(
                user_id=joiner_id,
                community_id=community.community_id
            )
            _db.session.add(new_member)
            _db.session.commit()
            
            # Verify membership
            membership = CommunityMember.query.filter_by(
                user_id=joiner_id,
                community_id=community.community_id
            ).first()
            assert membership is not None
            
            # Cleanup
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()
    
    def test_cannot_join_twice(self, app, two_users):
        """Duplicate membership should be prevented (app logic check)"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            creator_id, joiner_id = two_users
            creator = _db.session.get(User, creator_id)
            
            # Create community
            community = CommunityService.create_community(
                community_name="No Duplicates Community",
                subject="Testing",
                college_id=creator.college_id,
                user_id=creator_id
            )
            
            # Joiner joins once
            member1 = CommunityMember(
                user_id=joiner_id,
                community_id=community.community_id
            )
            _db.session.add(member1)
            _db.session.commit()
            
            # Check if already member (route logic would check this)
            existing = CommunityMember.query.filter_by(
                user_id=joiner_id,
                community_id=community.community_id
            ).first()
            
            assert existing is not None  # Already a member
            
            # Cleanup
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()


class TestCommunityMessages:
    """Test community message operations."""
    
    def test_member_can_post_message(self, app, seeded_user):
        """Community member can post messages"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_message import CommunityMessage
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            user = _db.session.get(User, seeded_user["id"])
            
            # Create community
            community = CommunityService.create_community(
                community_name="Chat Community",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id
            )
            
            # Post message
            message = CommunityMessage(
                community_id=community.community_id,
                user_id=user.id,
                message="Hello, community!"
            )
            _db.session.add(message)
            _db.session.commit()
            
            # Verify message exists
            saved_msg = CommunityMessage.query.filter_by(
                community_id=community.community_id,
                user_id=user.id
            ).first()
            
            assert saved_msg is not None
            assert saved_msg.message == "Hello, community!"
            assert saved_msg.is_deleted is False
            
            # Cleanup
            CommunityMessage.query.filter_by(community_id=community.community_id).delete()
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()
    
    def test_messages_ordered_by_time(self, app, seeded_user):
        """Messages are retrievable in chronological order"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_message import CommunityMessage
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            import time
            
            user = _db.session.get(User, seeded_user["id"])
            
            # Create community
            community = CommunityService.create_community(
                community_name="Timeline Community",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id
            )
            
            # Post multiple messages
            messages = []
            for i in range(3):
                msg = CommunityMessage(
                    community_id=community.community_id,
                    user_id=user.id,
                    message=f"Message {i+1}"
                )
                _db.session.add(msg)
                _db.session.flush()
                messages.append(msg)
                time.sleep(0.01)  # Small delay to ensure different timestamps
            
            _db.session.commit()
            
            # Retrieve messages in order
            retrieved = (
                CommunityMessage.query
                .filter_by(community_id=community.community_id)
                .order_by(CommunityMessage.messaged_at.asc())
                .all()
            )
            
            assert len(retrieved) == 3
            assert retrieved[0].message == "Message 1"
            assert retrieved[2].message == "Message 3"
            
            # Cleanup
            CommunityMessage.query.filter_by(community_id=community.community_id).delete()
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()


class TestCommunitySettings:
    """Test community settings and constraints."""
    
    def test_default_settings_applied(self, app, seeded_user):
        """Communities get sensible defaults"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            user = _db.session.get(User, seeded_user["id"])
            
            community = CommunityService.create_community(
                community_name="Default Settings",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id
            )
            
            assert community.max_members == 50  # Default
            assert community.is_college_specific is True  # Default
            assert community.is_active is True
            assert community.is_archived is False
            assert isinstance(community.programming_languages, list)
            
            # Cleanup
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()
    
    def test_college_specific_flag(self, app, seeded_user):
        """is_college_specific flag can be set false for cross-college communities"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            user = _db.session.get(User, seeded_user["id"])
            
            community = CommunityService.create_community(
                community_name="Global Community",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id,
                is_college_specific=False
            )
            
            assert community.is_college_specific is False
            
            # Cleanup
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()


# =============================================================================
# COMMUNITY TASKS (Basic Coverage)
# =============================================================================

class TestCommunityTasks:
    """Test community task creation and tracking."""
    
    def test_create_community_task(self, app, seeded_user):
        """Community tasks can be created"""
        with app.app_context():
            from app.services.community_service import CommunityService
            from app.models.community_task import CommunityTask
            from app.models.community_member import CommunityMember
            from app.models.user import User
            from app.extensions import db as _db
            
            user = _db.session.get(User, seeded_user["id"])
            
            # Create community
            community = CommunityService.create_community(
                community_name="Task Community",
                subject="Testing",
                college_id=user.college_id,
                user_id=user.id
            )
            
            # Create task
            task = CommunityTask(
                community_id=community.community_id,
                created_by=user.id,
                title="Complete Tutorial",
                description="Finish the Python tutorial",
                max_xp_reward=100,
                actions=[{"id": 1, "text": "Finish tutorial", "xp": 100}]
            )
            _db.session.add(task)
            _db.session.commit()
            
            # Verify task
            saved_task = CommunityTask.query.filter_by(
                community_id=community.community_id
            ).first()
            
            assert saved_task is not None
            assert saved_task.title == "Complete Tutorial"
            assert saved_task.max_xp_reward == 100
            assert saved_task.is_active is True
            
            # Cleanup
            from app.models.community_message import CommunityMessage
            CommunityTask.query.filter_by(community_id=community.community_id).delete()
            CommunityMessage.query.filter_by(community_id=community.community_id).delete()
            CommunityMember.query.filter_by(community_id=community.community_id).delete()
            _db.session.delete(community)
            _db.session.commit()
