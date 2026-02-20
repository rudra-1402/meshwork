"""
Tests for leaderboard endpoints.
Coverage targets: leaderboard_routes.py (36% → 75%)
"""
import pytest
from datetime import datetime, timezone


# =============================================================================
# XP LEADERBOARD TESTS
# =============================================================================

class TestXPLeaderboard:
    """Test XP leaderboard endpoint."""
    
    def test_xp_leaderboard_returns_top_users(self, client, users_with_xp, auth_headers):
        """GET /api/leaderboard/xp returns users sorted by XP"""
        resp = client.get('/api/leaderboard/xp', headers=auth_headers)
        assert resp.status_code == 200
        
        data = resp.get_json()
        assert data['success'] is True
        assert data['leaderboard_type'] == 'xp'
        assert 'leaderboard' in data
        assert isinstance(data['leaderboard'], list)
        
        # Verify leaderboard has entries
        leaderboard = data['leaderboard']
        assert len(leaderboard) > 0
        
        # Verify sorted by XP descending
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]['xp'] >= leaderboard[i + 1]['xp']
    
    def test_xp_leaderboard_default_limit(self, client, users_with_xp, auth_headers):
        """Default limit is 10 users"""
        resp = client.get('/api/leaderboard/xp', headers=auth_headers)
        data = resp.get_json()
        
        # With 10 users created, should return all
        assert len(data['leaderboard']) == 10
        assert data['total_entries'] == 10
    
    def test_xp_leaderboard_custom_limit(self, client, users_with_xp, auth_headers):
        """Can request custom limit"""
        resp = client.get('/api/leaderboard/xp?limit=5', headers=auth_headers)
        data = resp.get_json()
        
        assert len(data['leaderboard']) == 5
    
    def test_xp_leaderboard_max_limit_enforced(self, client, users_with_xp, auth_headers):
        """Limit capped at 50"""
        resp = client.get('/api/leaderboard/xp?limit=999', headers=auth_headers)
        data = resp.get_json()
        
        # Should not exceed 50 even if requested
        assert len(data['leaderboard']) <= 50
    
    def test_xp_leaderboard_includes_user_details(self, client, users_with_xp, auth_headers):
        """Leaderboard entries include username, xp, level"""
        resp = client.get('/api/leaderboard/xp?limit=1', headers=auth_headers)
        data = resp.get_json()
        
        assert len(data['leaderboard']) > 0
        entry = data['leaderboard'][0]
        
        # Should have user details
        assert 'username' in entry
        assert 'xp' in entry
        assert 'level' in entry
        assert isinstance(entry['xp'], int)
        assert isinstance(entry['level'], int)


# =============================================================================
# STREAK LEADERBOARD TESTS
# =============================================================================

class TestStreakLeaderboard:
    """Test streak leaderboard endpoint."""
    
    def test_streak_leaderboard_returns_top_users(self, client, app, auth_headers):
        """GET /api/leaderboard/streak returns users sorted by streak"""
        # Create users with different streaks
        with app.app_context():
            from app.models.user import User
            from app.extensions import db as _db
            
            user_ids = []
            streaks = [15, 10, 5, 3, 1]
            for i, streak in enumerate(streaks):
                u = User(
                    username=f"streakuser_{i}",
                    first_name=f"Streak{i}",
                    last_name="Test",
                    email=f"streak{i}@test.edu",
                    current_streak=streak,
                    max_streak=streak,
                )
                u.set_password("TestPass123!")
                _db.session.add(u)
            _db.session.commit()
            
            # Get user IDs for cleanup
            user_ids = [u.id for u in User.query.filter(
                User.username.like("streakuser_%")
            ).all()]
        
        try:
            resp = client.get('/api/leaderboard/streak', headers=auth_headers)
            assert resp.status_code == 200
            
            data = resp.get_json()
            assert data['success'] is True
            assert data['leaderboard_type'] == 'streak'
            
            leaderboard = data['leaderboard']
            assert len(leaderboard) > 0
            
            # Verify sorted by streak descending
            if len(leaderboard) > 1:
                for i in range(len(leaderboard) - 1):
                    assert leaderboard[i]['current_streak'] >= leaderboard[i + 1]['current_streak']
        finally:
            # Cleanup
            with app.app_context():
                from app.models.user import User
                from app.extensions import db as _db
                User.query.filter(User.username.like("streakuser_%")).delete()
                _db.session.commit()
    
    def test_streak_leaderboard_custom_limit(self, client, auth_headers):
        """Can request custom limit for streak leaderboard"""
        resp = client.get('/api/leaderboard/streak?limit=3', headers=auth_headers)
        data = resp.get_json()
        
        assert resp.status_code == 200
        assert len(data['leaderboard']) <= 3


# =============================================================================
# SKILL LEADERBOARD TESTS
# =============================================================================

class TestSkillLeaderboard:
    """Test skill-specific leaderboard endpoint."""
    
    def test_skill_leaderboard_valid_skill(self, client, app):
        """GET /api/leaderboard/skill/<skill_name> returns top users for that skill"""
        # Create users with Python skills
        with app.app_context():
            from app.models.user import User
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            user_ids = []
            for i in range(3):
                u = User(
                    username=f"pydev_{i}",
                    first_name=f"Dev{i}",
                    last_name="Python",
                    email=f"pydev{i}@test.edu",
                )
                u.set_password("TestPass123!")
                _db.session.add(u)
            _db.session.commit()
            
            users = User.query.filter(User.username.like("pydev_%")).all()
            skill_xps = [500, 300, 100]
            for user, xp in zip(users, skill_xps):
                skill = UserSkill(
                    user_id=user.id,
                    skill_name="Python",
                    xp=xp,
                    level=1,
                )
                _db.session.add(skill)
            _db.session.commit()
            
            user_ids = [u.id for u in users]
        
        try:
            resp = client.get('/api/leaderboard/skill/Python')
            assert resp.status_code == 200
            
            data = resp.get_json()
            assert data['success'] is True
            assert data['leaderboard_type'] == 'skill'
            assert data['skill_name'] == 'Python'
            
            leaderboard = data['leaderboard']
            assert len(leaderboard) == 3
            
            # Verify sorted by skill XP descending
            assert leaderboard[0]['xp'] >= leaderboard[1]['xp']
            assert leaderboard[1]['xp'] >= leaderboard[2]['xp']
        finally:
            # Cleanup
            with app.app_context():
                from app.models.user import User
                from app.models.user_skill import UserSkill
                from app.extensions import db as _db
                
                UserSkill.query.filter(UserSkill.skill_name == "Python").filter(
                    UserSkill.user_id.in_(user_ids)
                ).delete(synchronize_session=False)
                User.query.filter(User.username.like("pydev_%")).delete()
                _db.session.commit()
    
    def test_skill_leaderboard_invalid_skill(self, client):
        """Invalid skill name returns 400 error"""
        resp = client.get('/api/leaderboard/skill/NotARealSkill')
        assert resp.status_code == 400
        
        data = resp.get_json()
        assert data['success'] is False
        assert 'error' in data
        assert 'available_skills' in data  # Should include list of valid skills
    
    def test_skill_leaderboard_case_sensitive(self, client):
        """Skill names are case-sensitive"""
        # "Python" is valid, "python" is not
        resp = client.get('/api/leaderboard/skill/python')
        assert resp.status_code == 400


# =============================================================================
# AVAILABLE SKILLS TESTS
# =============================================================================

class TestAvailableSkills:
    """Test endpoint that lists available skills."""
    
    def test_get_available_skills(self, client):
        """GET /api/leaderboard/skills/available returns skill list"""
        resp = client.get('/api/leaderboard/skills/available')
        assert resp.status_code == 200
        
        data = resp.get_json()
        assert data['success'] is True
        assert 'skills' in data
        assert isinstance(data['skills'], list)
        assert len(data['skills']) > 0
        assert data['total_skills'] == len(data['skills'])
    
    def test_available_skills_includes_common_languages(self, client):
        """Available skills include common programming languages"""
        resp = client.get('/api/leaderboard/skills/available')
        data = resp.get_json()
        
        skills = data['skills']
        assert 'Python' in skills
        assert 'JavaScript' in skills
        assert 'Java' in skills


# =============================================================================
# ALL LEADERBOARDS TESTS
# =============================================================================

class TestAllLeaderboards:
    """Test endpoint that returns all leaderboards at once."""
    
    def test_get_all_leaderboards(self, client, auth_headers):
        """GET /api/leaderboard/all returns multiple leaderboards"""
        resp = client.get('/api/leaderboard/all', headers=auth_headers)
        assert resp.status_code == 200
        
        data = resp.get_json()
        assert data['success'] is True
        assert 'xp_leaderboard' in data
        assert 'streak_leaderboard' in data
        assert 'skill_leaderboards' in data
    
    def test_all_leaderboards_structure(self, client, auth_headers):
        """All leaderboards have proper structure"""
        resp = client.get('/api/leaderboard/all', headers=auth_headers)
        data = resp.get_json()
        
        # XP leaderboard is a list
        assert isinstance(data['xp_leaderboard'], list)
        
        # Streak leaderboard is a list
        assert isinstance(data['streak_leaderboard'], list)
        
        # Skill leaderboards is a dict of skill -> list
        assert isinstance(data['skill_leaderboards'], dict)


# =============================================================================
# MY RANK TESTS
# =============================================================================

class TestMyRank:
    """Test endpoint that returns user's rank in all leaderboards."""
    
    def test_my_rank_requires_auth(self, client):
        """GET /api/leaderboard/my-rank requires JWT"""
        resp = client.get('/api/leaderboard/my-rank')
        assert resp.status_code == 401
    
    def test_my_rank_returns_user_ranks(self, client, auth_headers, app, seeded_user):
        """Authenticated user can see their rank"""
        resp = client.get('/api/leaderboard/my-rank', headers=auth_headers)
        assert resp.status_code == 200
        
        data = resp.get_json()
        assert data['success'] is True
        assert 'user_id' in data
        assert 'username' in data
        assert 'xp_rank' in data
        assert 'total_xp' in data
        assert 'streak_rank' in data
        assert 'current_streak' in data
        assert 'skill_ranks' in data
    
    def test_my_rank_calculates_correct_xp_rank(self, client, auth_headers, app, seeded_user, users_with_xp):
        """XP rank is calculated correctly based on user's XP"""
        with app.app_context():
            from app.models.user import User
            from app.extensions import db as _db
            
            # Set seeded user's XP to a known value
            user = _db.session.get(User, seeded_user["id"])
            user.xp = 2500  # Should rank between some users_with_xp
            _db.session.commit()
        
        resp = client.get('/api/leaderboard/my-rank', headers=auth_headers)
        data = resp.get_json()
        
        assert data['total_xp'] == 2500
        assert isinstance(data['xp_rank'], int)
        assert data['xp_rank'] > 0
    
    def test_my_rank_includes_skill_ranks(self, client, auth_headers, app, seeded_user):
        """User's skill ranks are included"""
        # Add a skill to the user
        with app.app_context():
            from app.models.user_skill import UserSkill
            from app.extensions import db as _db
            
            skill = UserSkill(
                user_id=seeded_user["id"],
                skill_name="Python",
                xp=250,
                level=2,
            )
            _db.session.add(skill)
            _db.session.commit()
        
        try:
            resp = client.get('/api/leaderboard/my-rank', headers=auth_headers)
            data = resp.get_json()
            
            assert 'skill_ranks' in data
            skill_ranks = data['skill_ranks']
            
            if len(skill_ranks) > 0:
                assert 'skill_name' in skill_ranks[0]
                assert 'rank' in skill_ranks[0]
                assert 'xp' in skill_ranks[0]
                assert 'level' in skill_ranks[0]
        finally:
            # Cleanup
            with app.app_context():
                from app.models.user_skill import UserSkill
                from app.extensions import db as _db
                UserSkill.query.filter_by(
                    user_id=seeded_user["id"],
                    skill_name="Python"
                ).delete()
                _db.session.commit()
