"""
Tests for ScoringService (Gemini-powered AI scoring).

Gemini API is mocked at the google.genai.Client level so no real API calls occur.
Tests cover:
- ScoringService internal pure methods (no mock needed)
- process_initial_questionnaire (mocked Gemini)
- update_interest_scores_from_activity (no Gemini call needed)
- _validate_ai_response validation rules
- _normalize_scores normalization logic
- _select_dominant_roles tie-breaking
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from app.extensions import db
from app.services.scoring_service import ScoringService
from app.exceptions import ValidationError, AlreadyScoredError, ScoringError, NotScoredError


# =============================================================================
# HELPERS — shared test data
# =============================================================================

def make_valid_ai_response(motivation=7.5):
    """Return a valid AI response dict matching ScoringService schema."""
    roles = {
        "Builder": 8.0, "Architect": 6.5, "Problem Solver": 7.0, "Specialist": 5.0,
        "Designer": 4.0, "Product Thinker": 5.5, "Leader": 3.0, "Collaborator": 6.0,
        "Mentor": 2.5, "Explorer": 7.5
    }
    interests = {name: 5.0 for name in ScoringService.INTERESTS}
    # Give a few higher scores to make it interesting
    interests["Backend Development"] = 8.5
    interests["Machine Learning"] = 7.0
    interests["API Design"] = 6.5
    return {
        "motivation_score": motivation,
        "roles": roles,
        "interests": interests
    }


def make_mock_gemini_client(response_json=None):
    """Return a MagicMock that mimics google.genai.Client with generate_content."""
    if response_json is None:
        response_json = make_valid_ai_response()

    mock_response = MagicMock()
    mock_response.text = json.dumps(response_json)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def get_valid_questionnaire():
    """Return a valid questionnaire payload."""
    return {
        "q1_project_excitement": "I would love to build a distributed real-time platform that processes millions of events per second with automatic failover and load balancing.",
        "q2_team_roles": ["Building core features", "Designing architecture"],
        "q2_explanation": "I enjoy writing core logic and thinking about how systems fit together at a macro level.",
        "q3_depth_vs_breadth": 4,
        "q3_explanation": "I prefer going deep on backend systems while staying aware of the full stack.",
        "q4_problem_solving": "Breaking problems into the smallest reproducible case, then reasoning up from first principles",
        "q5_hackathons": 4,
        "q5_competitions": 2,
        "q5_team_projects": 5,
        "q5_open_source": 3,
        "q5_research": 1,
        "q6_technologies": ["Web (Backend)", "Cloud / DevOps", "Data"],
        "q7_collaboration_style": "I enjoy tight collaboration with a small team",
        "q7_explanation": "Small teams move fast and I can have real ownership of what I build.",
        "q8_learning_motivation": "Shipping software that solves real problems — seeing users actually use what I built keeps me going."
    }


# =============================================================================
# HELPER — create ScoringService with a mocked Gemini client
# =============================================================================

def make_scoring_service(mock_client=None):
    """
    Create a ScoringService with Gemini patched out.
    Patches both the Client constructor and GEMINI_API_KEY env var.
    """
    if mock_client is None:
        mock_client = make_mock_gemini_client()

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key-for-testing"}):
        with patch("app.services.scoring_service.genai.Client", return_value=mock_client):
            service = ScoringService()
    # Replace the client on the instance so it persists after the patch context
    service.client = mock_client
    return service


# =============================================================================
# PURE UNIT TESTS — internal helpers, no DB or Gemini needed
# =============================================================================

class TestSelectDominantRoles:
    """_select_dominant_roles: pure method — no DB needed."""

    def test_returns_top_4_roles(self):
        service = make_scoring_service()
        scores = {
            "Builder": 9.0, "Architect": 8.0, "Problem Solver": 7.0,
            "Specialist": 6.0, "Designer": 5.0, "Product Thinker": 4.0,
            "Leader": 3.0, "Collaborator": 2.0, "Mentor": 1.0, "Explorer": 0.5
        }
        result = service._select_dominant_roles(scores)
        assert result == ["Builder", "Architect", "Problem Solver", "Specialist"]

    def test_exactly_4_roles_returned(self):
        service = make_scoring_service()
        scores = {role: float(i) for i, role in enumerate(ScoringService.ROLES)}
        result = service._select_dominant_roles(scores)
        assert len(result) == 4

    def test_tie_broken_alphabetically(self):
        service = make_scoring_service()
        # All roles same score → alphabetical order
        scores = {role: 5.0 for role in ScoringService.ROLES}
        result = service._select_dominant_roles(scores)
        # First 4 alphabetically out of the ROLES list
        expected = sorted(ScoringService.ROLES)[:4]
        assert result == expected


class TestNormalizeScores:
    """_normalize_scores: pure method."""

    def test_inflated_scores_scaled_down(self):
        service = make_scoring_service()
        roles = {role: 8.0 for role in ScoringService.ROLES}  # Sum = 80.0 > 70.0
        raw = {
            "motivation_score": 7.0,
            "roles": roles,
            "interests": {i: 5.0 for i in ScoringService.INTERESTS}
        }
        result = service._normalize_scores(raw)
        total = sum(result["roles"].values())
        assert total <= 70.0, f"Expected total ≤ 70, got {total}"

    def test_more_than_2_high_roles_capped(self):
        service = make_scoring_service()
        roles = {role: 9.0 for role in ScoringService.ROLES}  # All 9.0
        raw = {
            "motivation_score": 7.0,
            "roles": roles,
            "interests": {i: 5.0 for i in ScoringService.INTERESTS}
        }
        result = service._normalize_scores(raw)
        high_count = sum(1 for v in result["roles"].values() if v > 8.0)
        assert high_count <= 2

    def test_normal_scores_unchanged_in_structure(self):
        service = make_scoring_service()
        roles = {role: 5.0 for role in ScoringService.ROLES}  # Sum = 50.0, fine
        raw = {
            "motivation_score": 6.5,
            "roles": roles,
            "interests": {i: 4.0 for i in ScoringService.INTERESTS}
        }
        result = service._normalize_scores(raw)
        assert set(result["roles"].keys()) == set(ScoringService.ROLES)
        assert set(result["interests"].keys()) == set(ScoringService.INTERESTS)
        assert result["motivation_score"] == 6.5

    def test_scores_rounded_to_2_decimal_places(self):
        service = make_scoring_service()
        roles = {role: 5.123456 for role in ScoringService.ROLES}
        raw = {
            "motivation_score": 7.123456,
            "roles": roles,
            "interests": {i: 3.987654 for i in ScoringService.INTERESTS}
        }
        result = service._normalize_scores(raw)
        for score in result["roles"].values():
            assert round(score, 2) == score
        for score in result["interests"].values():
            assert round(score, 2) == score


class TestValidateAIResponse:
    """_validate_ai_response: pure method."""

    def test_valid_response_passes(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        result = service._validate_ai_response(data)
        assert result == data

    def test_missing_top_level_key_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        del data["motivation_score"]
        with pytest.raises(ValidationError, match="missing keys"):
            service._validate_ai_response(data)

    def test_motivation_score_out_of_range_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        data["motivation_score"] = 11.0  # > 10
        with pytest.raises(ValidationError, match="out of range"):
            service._validate_ai_response(data)

    def test_motivation_score_negative_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        data["motivation_score"] = -1.0
        with pytest.raises(ValidationError, match="out of range"):
            service._validate_ai_response(data)

    def test_missing_role_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        del data["roles"]["Builder"]  # Remove one role
        with pytest.raises(ValidationError, match="Role mismatch"):
            service._validate_ai_response(data)

    def test_extra_role_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        data["roles"]["FakeRole"] = 5.0
        with pytest.raises(ValidationError, match="Role mismatch"):
            service._validate_ai_response(data)

    def test_role_score_out_of_range_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        data["roles"]["Builder"] = 12.0
        with pytest.raises(ValidationError, match="out of range"):
            service._validate_ai_response(data)

    def test_missing_interest_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        del data["interests"]["Backend Development"]
        with pytest.raises(ValidationError, match="Interest mismatch"):
            service._validate_ai_response(data)

    def test_non_numeric_role_score_fails(self):
        service = make_scoring_service()
        data = make_valid_ai_response()
        data["roles"]["Builder"] = "high"
        with pytest.raises(ValidationError, match="must be numeric"):
            service._validate_ai_response(data)


class TestGetTopN:
    """_get_top_n_from_dict: pure method."""

    def test_returns_correct_count(self):
        service = make_scoring_service()
        scores = {"A": 9.0, "B": 7.0, "C": 5.0, "D": 3.0, "E": 1.0}
        result = service._get_top_n_from_dict(scores, n=3)
        assert len(result) == 3

    def test_sorted_by_score_descending(self):
        service = make_scoring_service()
        scores = {"A": 3.0, "B": 9.0, "C": 6.0}
        result = service._get_top_n_from_dict(scores, n=3)
        assert result[0]["name"] == "B"
        assert result[1]["name"] == "C"
        assert result[2]["name"] == "A"

    def test_result_structure(self):
        service = make_scoring_service()
        scores = {"X": 5.0, "Y": 8.0}
        result = service._get_top_n_from_dict(scores, n=2)
        for item in result:
            assert "name" in item
            assert "score" in item
            assert isinstance(item["score"], float)


class TestFormatActivityDescription:
    """_format_activity_description: pure method."""

    def test_project_creation(self):
        service = make_scoring_service()
        desc = service._format_activity_description(
            "project_creation",
            {"project_name": "MyApp", "languages": ["Python", "React"]}
        )
        assert "MyApp" in desc
        assert "Python" in desc

    def test_project_completion(self):
        service = make_scoring_service()
        desc = service._format_activity_description(
            "project_completion",
            {"project_name": "MyApp"}
        )
        assert "MyApp" in desc

    def test_event_participation(self):
        service = make_scoring_service()
        desc = service._format_activity_description(
            "event_participation",
            {"event_name": "Hackathon 2026"}
        )
        assert "Hackathon 2026" in desc

    def test_unknown_activity(self):
        service = make_scoring_service()
        desc = service._format_activity_description("mystery_action", {})
        assert "mystery_action" in desc


# =============================================================================
# INTEGRATION TESTS — require DB + mocked Gemini
# =============================================================================

class TestProcessInitialQuestionnaire:
    """process_initial_questionnaire: mocked Gemini + real DB."""

    def test_success_returns_expected_structure(self, app, xp_user):
        with app.app_context():
            mock_client = make_mock_gemini_client(make_valid_ai_response())
            service = make_scoring_service(mock_client)

            result = service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            assert "dominant_roles" in result
            assert "motivation_score" in result
            assert "top_interests" in result
            assert len(result["dominant_roles"]) == 4
            assert 0.0 <= result["motivation_score"] <= 10.0
            assert len(result["top_interests"]) == 5

    def test_success_marks_questionnaire_completed(self, app, xp_user):
        with app.app_context():
            from app.models.user import User
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            user = db.session.get(User, xp_user)
            assert user.has_completed_questionnaire is True

    def test_success_creates_scoring_record(self, app, xp_user):
        with app.app_context():
            from app.models.scoring import UserScoring
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            record = UserScoring.query.filter_by(user_id=xp_user).first()
            assert record is not None
            assert len(record.dominant_roles) == 4

    def test_questionnaire_does_not_award_xp_or_level(self, app, xp_user):
        with app.app_context():
            from app.models.user import User

            user_before = db.session.get(User, xp_user)
            xp_before = user_before.xp
            level_before = user_before.level

            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            user_after = db.session.get(User, xp_user)
            assert user_after.xp == xp_before
            assert user_after.level == level_before

    def test_duplicate_raises_already_scored_error(self, app, xp_user):
        with app.app_context():
            service = make_scoring_service(make_mock_gemini_client())
            # First submission succeeds
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())
            # Second raises error (no Gemini call reached)
            with pytest.raises(AlreadyScoredError):
                service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

    def test_invalid_questionnaire_raises_validation_error(self, app, xp_user):
        with app.app_context():
            service = make_scoring_service(make_mock_gemini_client())
            bad_data = {"q1_project_excitement": "too short"}
            with pytest.raises(ValidationError):
                service.process_initial_questionnaire(xp_user, bad_data)

    def test_gemini_invalid_json_raises_scoring_error(self, app, xp_user):
        with app.app_context():
            mock_response = MagicMock()
            mock_response.text = "this is not json {"
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response

            service = make_scoring_service(mock_client)
            with pytest.raises(ScoringError, match="invalid JSON"):
                service.process_initial_questionnaire(xp_user, get_valid_questionnaire())


class TestUpdateInterestScores:
    """update_interest_scores_from_activity: requires prior initial scoring."""

    def _seed_initial_scoring(self, app, user_id):
        """Helper: run initial scoring for a user so updates can proceed."""
        service = make_scoring_service(make_mock_gemini_client())
        with app.app_context():
            service.process_initial_questionnaire(user_id, get_valid_questionnaire())

    def test_update_succeeds_after_initial_scoring(self, app, xp_user):
        with app.app_context():
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            result = service.update_interest_scores_from_activity(
                user_id=xp_user,
                activity_type="project_creation",
                activity_data={"project_name": "MyProject", "languages": ["Python"]},
                interest_adjustments={"Backend Development": 0.5}
            )

            assert "updated_interests" in result
            assert "top_interests" in result

    def test_update_without_initial_raises_not_scored_error(self, app, xp_user):
        with app.app_context():
            service = make_scoring_service(make_mock_gemini_client())
            with pytest.raises(NotScoredError):
                service.update_interest_scores_from_activity(
                    user_id=xp_user,
                    activity_type="project_creation",
                    activity_data={},
                    interest_adjustments={"Backend Development": 0.5}
                )

    def test_invalid_interest_name_raises_validation_error(self, app, xp_user):
        with app.app_context():
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            with pytest.raises(ValidationError, match="Invalid interest names"):
                service.update_interest_scores_from_activity(
                    user_id=xp_user,
                    activity_type="project_creation",
                    activity_data={},
                    interest_adjustments={"NotARealInterest": 1.0}
                )

    def test_score_capped_at_10(self, app, xp_user):
        with app.app_context():
            from app.models.scoring import UserScoring
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            # Apply a huge delta — should cap at 10.0
            service.update_interest_scores_from_activity(
                user_id=xp_user,
                activity_type="project_creation",
                activity_data={},
                interest_adjustments={"Backend Development": 999.0}
            )

            record = UserScoring.query.filter_by(user_id=xp_user).first()
            assert record.interest_scores["Backend Development"] <= 10.0

    def test_score_floored_at_0(self, app, xp_user):
        with app.app_context():
            from app.models.scoring import UserScoring
            service = make_scoring_service(make_mock_gemini_client())
            service.process_initial_questionnaire(xp_user, get_valid_questionnaire())

            # Apply a huge negative delta — should floor at 0.0
            service.update_interest_scores_from_activity(
                user_id=xp_user,
                activity_type="project_creation",
                activity_data={},
                interest_adjustments={"Backend Development": -999.0}
            )

            record = UserScoring.query.filter_by(user_id=xp_user).first()
            assert record.interest_scores["Backend Development"] >= 0.0
