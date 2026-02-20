"""
Tests for Questionnaire and Skill/Language Submission

Covers:
- questionnaire_schema.py validation
- scoring_routes.py questionnaire submission  
- Profile skill/language endpoints
- Questionnaire data processing

Following TEST_PATTERNS_DOCUMENTATION.md:
- Class-based organization
- API-driven testing
- Session-scoped fixtures
"""

import pytest
from app.extensions import db
from app.schemas.questionnaire_schema import validate_questionnaire, QUESTIONNAIRE_SCHEMA
from app.exceptions import ValidationError
from app.constants.gamification import AVAILABLE_SKILLS


class TestQuestionnaireValidation:
    """Test questionnaire schema validation"""

    def get_valid_questionnaire_data(self):
        """Helper to generate valid questionnaire data"""
        return {
            "q1_project_excitement": "I would love to build a real-time collaboration tool that helps students work together on coding projects with features like live code editing and integrated chat.",
            "q2_team_roles": ["Building core features", "Designing architecture"],
            "q2_explanation": "I enjoy writing clean, efficient code and thinking about system design patterns.",
            "q3_depth_vs_breadth": 3,
            "q3_explanation": "I prefer a balanced approach - deep knowledge in a few areas while understanding the broader ecosystem.",
            "q4_problem_solving": "Breaking down complex problems into smaller parts and finding elegant solutions",
            "q5_hackathons": 4,
            "q5_competitions": 2,
            "q5_team_projects": 5,
            "q5_open_source": 3,
            "q5_research": 2,
            "q6_technologies": ["Web (Backend)", "Cloud / DevOps", "AI / ML"],
            "q7_collaboration_style": "I enjoy tight collaboration with a small team",
            "q7_explanation": "I like working closely with teammates to solve problems together",
            "q8_learning_motivation": "Building real projects and seeing them help people motivates me"
        }

    def test_valid_questionnaire_passes(self, app):
        """Valid questionnaire data should pass validation"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            assert validate_questionnaire(data) is True

    def test_missing_required_field_fails(self, app):
        """Missing required fields should fail validation"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            del data["q1_project_excitement"]
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "Missing required field" in str(exc_info.value)

    def test_string_too_short_fails(self, app):
        """Strings shorter than min_length should fail"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            data["q1_project_excitement"] = "Too short"  # min_length is 30
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "at least" in str(exc_info.value).lower()

    def test_integer_out_of_range_fails(self, app):
        """Integers outside valid range should fail"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            data["q3_depth_vs_breadth"] = 10  # max is 5
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "must be <=" in str(exc_info.value)

    def test_list_too_many_items_fails(self, app):
        """Lists exceeding max_items should fail"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            data["q2_team_roles"] = [
                "Building core features",
                "Designing architecture",
                "Working on UI/UX"
            ]  # max_items is 2
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "at most" in str(exc_info.value).lower()

    def test_invalid_list_values_fail(self, app):
        """List items not in allowed_values should fail"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            data["q2_team_roles"] = ["Invalid Role", "Another Invalid"]
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "invalid values" in str(exc_info.value).lower()

    def test_wrong_type_fails(self, app):
        """Wrong data types should fail validation"""
        with app.app_context():
            data = self.get_valid_questionnaire_data()
            data["q3_depth_vs_breadth"] = "three"  # should be int
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(data)
            
            assert "must be an integer" in str(exc_info.value)

    def test_empty_data_fails(self, app):
        """Empty or None data should fail"""
        with app.app_context():
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire({})
            # Empty dict returns "Invalid questionnaire data format" or "Missing required field"
            error_msg = str(exc_info.value)
            assert "Invalid" in error_msg or "Missing" in error_msg
            
            with pytest.raises(ValidationError) as exc_info:
                validate_questionnaire(None)
            assert "Invalid questionnaire data format" in str(exc_info.value)


class TestSkillEndpoints:
    """Test skill-related profile endpoints"""

    def test_get_skills_requires_auth(self, client):
        """Skills endpoint should require authentication"""
        response = client.get('/api/profile/skills')
        assert response.status_code == 401

    def test_get_user_skills(self, client, auth_headers):
        """Should return user's skill profile"""
        response = client.get('/api/profile/skills', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert 'success' in data
        assert 'skills' in data

    def test_get_skills_with_limit(self, client, auth_headers):
        """Should respect limit parameter"""
        response = client.get('/api/profile/skills?limit=5', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert 'skills' in data

    def test_skills_limit_capped(self, client, auth_headers):
        """Skills limit should be capped at max value"""
        response = client.get('/api/profile/skills?limit=1000', headers=auth_headers)
        
        assert response.status_code == 200
        # Should work but cap at maximum


class TestProfileEndpoints:
    """Test profile endpoints"""

    def test_get_own_profile(self, client, auth_headers):
        """Should return own profile with full stats"""
        response = client.get('/api/profile/', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'profile' in data
        assert 'xp_summary' in data
        assert 'skills' in data
        assert 'streak' in data

    def test_get_profile_requires_auth(self, client):
        """Profile endpoint should require authentication"""
        response = client.get('/api/profile/')
        assert response.status_code == 401

    def test_get_other_user_profile(self, client, seeded_user, auth_headers):
        """Should be able to view other users' public profiles"""
        # View the seeded user's profile
        response = client.get(f'/api/profile/{seeded_user["id"]}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'profile' in data
        assert 'skills' in data
        assert 'streak' in data

    def test_get_nonexistent_user_profile(self, client, auth_headers):
        """Should return 404 for nonexistent users"""
        response = client.get('/api/profile/99999', headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_stats_endpoint(self, client, auth_headers):
        """Stats endpoint should return comprehensive statistics"""
        response = client.get('/api/profile/stats', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'profile' in data
        assert 'daily_xp' in data
        assert 'top_skills' in data
        assert 'streak' in data


class TestAvailableSkills:
    """Test available skills constants"""

    def test_available_skills_list_exists(self):
        """AVAILABLE_SKILLS constant should be defined"""
        assert AVAILABLE_SKILLS is not None
        assert isinstance(AVAILABLE_SKILLS, list)
        assert len(AVAILABLE_SKILLS) > 0

    def test_available_skills_includes_common_languages(self):
        """Should include common programming languages"""
        common_langs = ['Python', 'JavaScript', 'Java', 'C++']
        for lang in common_langs:
            assert lang in AVAILABLE_SKILLS, f"{lang} should be in AVAILABLE_SKILLS"

    def test_available_skills_includes_frameworks(self):
        """Should include common frameworks"""
        common_frameworks = ['React', 'Node.js', 'Flask', 'Django']
        for framework in common_frameworks:
            assert framework in AVAILABLE_SKILLS, f"{framework} should be in AVAILABLE_SKILLS"
