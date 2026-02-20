import uuid
from datetime import datetime, timezone, timedelta

import pytest
from flask_jwt_extended import create_access_token


# -----------------------------------------------------------------------------
# Missing SUCCESS case routes (from coverage report)
# -----------------------------------------------------------------------------

def _future_iso(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def test_success_auth_login_route(client, seeded_user):
    resp = client.post(
        "/api/auth/login",
        json={"email": seeded_user["email"], "password": seeded_user["password"]},
    )
    assert resp.status_code == 200


def test_success_auth_signup_route(client, seeded_user):
    uid = uuid.uuid4().hex[:8]
    resp = client.post(
        "/api/auth/signup",
        json={
            "email": f"new_personnel_{uid}@test.edu",
            "password": "Pass@12345",
            "first_name": "New",
            "last_name": "Personnel",
            "user_type": "personnel",
            "college_id": seeded_user["college_id"],
            "role": "faculty",
        },
    )
    assert resp.status_code == 201


def test_success_validate_email_route(client, monkeypatch):
    from app.services.unified_auth_service import UnifiedAuthService

    monkeypatch.setattr(
        UnifiedAuthService,
        "validate_email_realtime",
        staticmethod(lambda email: {"valid": True, "user_type": "student", "college_id": 1}),
    )

    resp = client.post(
        "/api/auth/validate-email",
        json={"email": "student@example.edu"},
    )
    assert resp.status_code == 200


def test_success_communities_create_explore_view_join(client, app, auth_headers, seeded_user):
    create_resp = client.post(
        "/api/communities/create",
        json={"community_name": "Contract Community", "subject": "Testing"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    community_id = create_resp.get_json()["community"]["community_id"]

    explore_resp = client.get("/api/communities/explore", headers=auth_headers)
    assert explore_resp.status_code == 200

    view_resp = client.get(f"/api/communities/view/{community_id}", headers=auth_headers)
    assert view_resp.status_code == 200

    with app.app_context():
        from app.extensions import db as _db
        from app.models.user import User
        u = User(
            username=f"joiner_{uuid.uuid4().hex[:8]}",
            first_name="Join",
            last_name="User",
            email=f"joiner_{uuid.uuid4().hex[:8]}@test.local",
            college_id=seeded_user["college_id"],
        )
        u.set_password("Pass@12345")
        _db.session.add(u)
        _db.session.commit()
        joiner_id = u.id

        token = create_access_token(identity=str(joiner_id))
        join_headers = {"Authorization": f"Bearer {token}"}

    join_resp = client.post(f"/api/communities/join/{community_id}", headers=join_headers)
    assert join_resp.status_code == 200

    with app.app_context():
        from app.extensions import db as _db
        from app.models.community import Community
        from app.models.community_member import CommunityMember
        from app.models.community_message import CommunityMessage
        from app.models.user import User

        CommunityMessage.query.filter_by(community_id=community_id).delete()
        CommunityMember.query.filter_by(community_id=community_id).delete()
        community = _db.session.get(Community, community_id)
        if community:
            _db.session.delete(community)
        joiner = _db.session.get(User, joiner_id)
        if joiner:
            _db.session.delete(joiner)
        _db.session.commit()


def test_success_events_submit_route(client, personnel_user, personnel_auth_headers):
    with client.application.app_context():
        from app.services.event_service import EventService
        from app.constants.event_constants import EventCreatorType
        from app.extensions import db as _db

        payload = {
            "event_name": "Contract Submit Event",
            "description": "Contract coverage event",
            "event_type": "hackathon",
            "creator_type": EventCreatorType.COLLEGE,
            "creator_entity_id": personnel_user["college_id"],
            "is_college_specific": True,
            "college_id": personnel_user["college_id"],
            "start_time": _future_iso(1),
            "end_time": _future_iso(2),
        }
        success, msg, event = EventService.create_event(personnel_user["id"], payload)
        assert success, msg
        event_id = event.event_id
        _db.session.expunge(event)

    resp = client.post(f"/api/events/{event_id}/submit", headers=personnel_auth_headers)
    assert resp.status_code == 200


def test_success_project_get_update_fork_delete_routes(client, auth_headers, project_factory, monkeypatch):
    from app.services.project_service import ProjectService
    from types import SimpleNamespace

    project = project_factory(title="Contract Project", status="Open")
    pid = project["id"]

    get_resp = client.get(f"/api/projects/{pid}", headers=auth_headers)
    assert get_resp.status_code == 200

    update_resp = client.patch(
        f"/api/projects/{pid}",
        json={"title": "Contract Project Updated"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200

    monkeypatch.setattr(
        ProjectService,
        "fork_project",
        staticmethod(
            lambda source_project_id, forking_user_id: (
                True,
                "Project forked",
                SimpleNamespace(
                    id=99999,
                    title="Forked Project",
                    description="fork",
                    interest_tags=[],
                    forked_from_id=source_project_id,
                    fork_count=0,
                    status=SimpleNamespace(value="Draft"),
                    visibility=SimpleNamespace(value="public"),
                    membership_policy=SimpleNamespace(value="open"),
                    creator_id=forking_user_id,
                    parent_project_id=source_project_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    members=[],
                    languages=[],
                ),
            )
        ),
    )

    with client.application.app_context():
        fork_token = create_access_token(identity="1")

    fork_resp = client.post(
        f"/api/projects/{pid}/fork",
        headers={"Authorization": f"Bearer {fork_token}"},
    )
    assert fork_resp.status_code == 201

    delete_resp = client.delete(f"/api/projects/{pid}", headers=auth_headers)
    assert delete_resp.status_code == 200



# -----------------------------------------------------------------------------
# Missing FAILURE case routes (from coverage report)
# -----------------------------------------------------------------------------

def test_failure_events_list_route_no_auth(client):
    resp = client.get("/api/events/")
    assert resp.status_code == 401


def test_failure_leaderboard_all_no_auth(client):
    resp = client.get("/api/leaderboard/all")
    assert resp.status_code == 401


def test_failure_leaderboard_skills_available_bad_method(client):
    resp = client.post("/api/leaderboard/skills/available")
    assert resp.status_code == 405


def test_failure_leaderboard_streak_no_auth(client):
    resp = client.get("/api/leaderboard/streak")
    assert resp.status_code == 401


def test_failure_leaderboard_xp_no_auth(client):
    resp = client.get("/api/leaderboard/xp")
    assert resp.status_code == 401


def test_failure_profile_stats_no_auth(client):
    resp = client.get("/api/profile/stats")
    assert resp.status_code == 401


# -----------------------------------------------------------------------------
# Uncovered public routes
# -----------------------------------------------------------------------------

def test_public_root_and_health_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/api/").status_code == 200
    assert client.get("/api/health").status_code == 200


def test_public_check_username_route(client):
    ok = client.post("/api/auth/check-username", json={"username": f"name_{uuid.uuid4().hex[:6]}"})
    assert ok.status_code == 200

    bad = client.post("/api/auth/check-username", json={})
    assert bad.status_code == 400


def test_public_college_auth_routes(client):
    login_bad = client.post("/api/college-auth/login", json={})
    assert login_bad.status_code == 400

    uid = uuid.uuid4().hex[:8]
    signup_ok = client.post(
        "/api/college-auth/signup",
        json={
            "name": f"Contract College {uid}",
            "email": f"contract_college_{uid}@test.edu",
            "password": "Pass@12345",
            "confirm_password": "Pass@12345",
            "city": "Chennai",
            "state": "Tamil Nadu",
        },
    )
    assert signup_ok.status_code == 201


# -----------------------------------------------------------------------------
# Uncovered protected routes — unauthenticated failure contract
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/admin/bonus/1"),
        ("POST", "/api/admin/bulk-bonus"),
        ("POST", "/api/admin/penalty/1"),
        ("POST", "/api/admin/skill-xp/1"),
        ("GET", "/api/admin/user-stats/1"),
        ("GET", "/api/communities/1/tasks"),
        ("POST", "/api/communities/1/tasks/create"),
        ("POST", "/api/communities/message/1"),
        ("GET", "/api/dashboard/dashboard"),
        ("GET", "/api/dashboard/dashboard/college"),
        ("GET", "/api/dashboard/profile"),
        ("GET", "/api/events/1"),
        ("POST", "/api/events/1/approve"),
        ("POST", "/api/events/1/cancel"),
        ("POST", "/api/events/1/complete"),
        ("POST", "/api/events/1/confirm-attendance"),
        ("POST", "/api/events/1/drop"),
        ("GET", "/api/events/1/participants"),
        ("POST", "/api/events/1/register"),
        ("POST", "/api/events/1/reject"),
        ("GET", "/api/events/1/tasks"),
        ("POST", "/api/events/1/tasks"),
        ("POST", "/api/events/create"),
        ("GET", "/api/events/pending"),
        ("POST", "/api/events/tasks/1/submit-action"),
        ("GET", "/api/events/tasks/1/summary"),
        ("GET", "/api/personnel/college/email-config"),
        ("PATCH", "/api/personnel/college/email-config"),
        ("GET", "/api/personnel/dashboard"),
        ("GET", "/api/personnel/profile"),
        ("GET", "/api/personnel/students"),
        ("GET", "/api/personnel/whitelist"),
        ("POST", "/api/personnel/whitelist/add-single"),
        ("POST", "/api/personnel/whitelist/bulk-add"),
        ("POST", "/api/personnel/whitelist/remove/1"),
        ("GET", "/api/profile/level-progress"),
        ("GET", "/api/profile/streak-status"),
        ("GET", "/api/profile/xp-history"),
        ("POST", "/api/projects/1/members"),
        ("DELETE", "/api/projects/1/members/1"),
        ("PATCH", "/api/projects/1/members/1"),
        ("GET", "/api/scoring/history"),
        ("GET", "/api/scoring/profile"),
        ("GET", "/api/scoring/questionnaire"),
        ("POST", "/api/scoring/retake"),
        ("POST", "/api/scoring/submit"),
    ],
)
def test_uncovered_protected_routes_require_auth(client, method, path):
    method = method.upper()
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json={})
    elif method == "PATCH":
        resp = client.patch(path, json={})
    elif method == "DELETE":
        resp = client.delete(path)
    else:
        raise AssertionError(f"Unsupported method in test matrix: {method}")

    assert resp.status_code == 401
