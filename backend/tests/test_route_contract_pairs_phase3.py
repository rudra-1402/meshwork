from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from flask_jwt_extended import create_access_token


def _set_admin(app, user_id):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.user import User
        user = _db.session.get(User, user_id)
        user.is_admin = True
        _db.session.commit()


# -----------------------------------------------------------------------------
# Remaining failure-case contracts
# -----------------------------------------------------------------------------


def test_failure_root_wrong_method(client):
    assert client.post("/").status_code == 405


def test_failure_api_root_wrong_method(client):
    assert client.post("/api/").status_code == 405


def test_failure_health_wrong_method(client):
    assert client.post("/api/health").status_code == 405


def test_failure_available_skills_wrong_method(client):
    assert client.post("/api/leaderboard/skills/available").status_code == 405


# -----------------------------------------------------------------------------
# Admin success contracts
# -----------------------------------------------------------------------------


def test_success_admin_bonus_route(client, app, seeded_user, auth_headers, monkeypatch):
    _set_admin(app, seeded_user["id"])

    from app.services.xp_service import XPService
    monkeypatch.setattr(
        XPService,
        "award_xp",
        staticmethod(lambda **kwargs: {"xp_awarded": kwargs.get("amount", 0)}),
    )

    resp = client.post(
        f"/api/admin/bonus/{seeded_user['id']}",
        headers=auth_headers,
        json={"amount": 10, "reason": "bonus"},
    )
    assert resp.status_code == 200


def test_success_admin_penalty_route(client, app, seeded_user, auth_headers, monkeypatch):
    _set_admin(app, seeded_user["id"])

    from app.services.xp_service import XPService
    monkeypatch.setattr(
        XPService,
        "remove_xp",
        staticmethod(lambda **kwargs: {"xp_removed": kwargs.get("amount", 0)}),
    )

    resp = client.post(
        f"/api/admin/penalty/{seeded_user['id']}",
        headers=auth_headers,
        json={"amount": 5, "reason": "penalty"},
    )
    assert resp.status_code == 200


def test_success_admin_skill_xp_route(client, app, seeded_user, auth_headers, monkeypatch):
    _set_admin(app, seeded_user["id"])

    from app.services.skill_service import SkillService
    monkeypatch.setattr(
        SkillService,
        "award_skill_xp",
        staticmethod(lambda **kwargs: {"success": True, "xp": kwargs.get("amount", 0)}),
    )

    resp = client.post(
        f"/api/admin/skill-xp/{seeded_user['id']}",
        headers=auth_headers,
        json={"skill_name": "Python", "amount": 25, "reason": "manual"},
    )
    assert resp.status_code == 200


def test_success_admin_bulk_bonus_route(client, app, seeded_user, auth_headers, monkeypatch):
    _set_admin(app, seeded_user["id"])

    from app.services.xp_service import XPService
    monkeypatch.setattr(
        XPService,
        "award_xp",
        staticmethod(lambda **kwargs: {"success": True, "xp_awarded": kwargs.get("amount", 0)}),
    )

    resp = client.post(
        "/api/admin/bulk-bonus",
        headers=auth_headers,
        json={"user_ids": [seeded_user["id"]], "amount": 5, "reason": "bulk"},
    )
    assert resp.status_code == 200


def test_success_admin_user_stats_route(client, app, seeded_user, auth_headers, monkeypatch):
    _set_admin(app, seeded_user["id"])

    from app.services.xp_service import XPService
    from app.services.skill_service import SkillService
    from app.models.xp_transaction import XPTransaction

    monkeypatch.setattr(XPService, "get_daily_summary", staticmethod(lambda user: {"today": 0}))
    monkeypatch.setattr(SkillService, "get_user_skill_profile", staticmethod(lambda uid, limit=20: {"skills": []}))
    monkeypatch.setattr(XPTransaction, "get_user_history", staticmethod(lambda uid, limit=20: []))

    resp = client.get(f"/api/admin/user-stats/{seeded_user['id']}", headers=auth_headers)
    assert resp.status_code == 200


# -----------------------------------------------------------------------------
# Dashboard success contracts
# -----------------------------------------------------------------------------


def test_success_dashboard_routes(client, auth_headers):
    assert client.get("/api/dashboard/dashboard", headers=auth_headers).status_code == 200
    assert client.get("/api/dashboard/profile", headers=auth_headers).status_code == 200


def test_success_dashboard_college_route(client, app, seeded_user):
    with app.app_context():
        token = create_access_token(identity=f"college_{seeded_user['college_id']}")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/dashboard/dashboard/college", headers=headers)
    assert resp.status_code == 200


# -----------------------------------------------------------------------------
# Personnel success contracts
# -----------------------------------------------------------------------------


def test_success_personnel_core_routes(client, personnel_auth_headers):
    assert client.get("/api/personnel/dashboard", headers=personnel_auth_headers).status_code == 200
    assert client.get("/api/personnel/profile", headers=personnel_auth_headers).status_code == 200
    assert client.get("/api/personnel/students", headers=personnel_auth_headers).status_code == 200


def test_success_personnel_whitelist_routes(client, app, personnel_user, personnel_auth_headers):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.college_personnel import CollegePersonnel
        p = _db.session.get(CollegePersonnel, personnel_user["id"])
        p.can_manage_students = True
        p.can_manage_personnel = True
        _db.session.commit()

    assert client.get("/api/personnel/whitelist", headers=personnel_auth_headers).status_code == 200

    add_resp = client.post(
        "/api/personnel/whitelist/add-single",
        headers=personnel_auth_headers,
        json={"email": f"phase3_{personnel_user['id']}@test.edu"},
    )
    assert add_resp.status_code in (201, 400)

    with app.app_context():
        from app.extensions import db as _db
        from app.models.whitelisted_email import WhitelistedEmail
        WhitelistedEmail.query.filter_by(added_by_personnel_id=personnel_user["id"]).delete()
        _db.session.commit()

    assert client.get("/api/personnel/college/email-config", headers=personnel_auth_headers).status_code == 200

    patch_resp = client.patch(
        "/api/personnel/college/email-config",
        headers=personnel_auth_headers,
        json={
            "domain": f"college{personnel_user['id']}.edu",
            "student_email_pattern": "{enrollment}@college.edu",
            "personnel_email_pattern": "{personnel_id}-{role}@college.edu",
        },
    )
    assert patch_resp.status_code in (200, 400, 409)


# -----------------------------------------------------------------------------
# Events success contracts (service-mocked for route contract coverage)
# -----------------------------------------------------------------------------


def test_success_events_route_matrix(client, auth_headers, personnel_auth_headers, monkeypatch):
    from app.services.event_service import EventService

    event = SimpleNamespace(
        event_id=1,
        event_name="Mock Event",
        description="desc",
        event_type="hackathon",
        status="active",
        creator_type="college",
        creator_entity_id=1,
        created_by=1,
        is_college_specific=True,
        college_id=1,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        registration_deadline=None,
        max_participants=100,
        programming_languages=["Python"],
        requirements={},
        completion_xp=10,
        is_verified=True,
        verified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    participant = SimpleNamespace(
        id=1,
        event_id=1,
        user_id=1,
        registration_status="registered",
        registered_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    task = SimpleNamespace(
        task_id=1,
        event_id=1,
        title="Task",
        description="D",
        difficulty="Easy",
        xp_reward=5,
        actions=[{"id": 1, "text": "a", "xp": 5}],
        is_required=False,
        created_at=datetime.now(timezone.utc),
    )
    completion = SimpleNamespace(
        id=1,
        event_task_id=1,
        user_id=1,
        action_id=1,
        status="approved",
        xp_awarded=5,
        submitted_at=datetime.now(timezone.utc),
        reviewed_at=datetime.now(timezone.utc),
    )

    monkeypatch.setattr(EventService, "create_event", staticmethod(lambda creator_id, data: (True, "ok", event)))
    monkeypatch.setattr(EventService, "submit_event_for_approval", staticmethod(lambda eid, cid, caller_is_personnel=False: (True, "ok", event)))
    monkeypatch.setattr(EventService, "approve_event", staticmethod(lambda eid, college_id: (True, "ok", event)))
    monkeypatch.setattr(EventService, "reject_event", staticmethod(lambda eid, college_id, reason: (True, "ok")))
    monkeypatch.setattr(EventService, "cancel_event", staticmethod(lambda eid, user_id=None, authority_college_id=None: (True, "ok")))
    monkeypatch.setattr(EventService, "complete_event", staticmethod(lambda eid, user_id=None, authority_college_id=None: (True, "ok")))
    monkeypatch.setattr(EventService, "register_for_event", staticmethod(lambda eid, uid: (True, "ok", participant)))
    monkeypatch.setattr(EventService, "confirm_attendance", staticmethod(lambda eid, uid: (True, "ok", participant)))
    monkeypatch.setattr(EventService, "drop_from_event", staticmethod(lambda eid, uid: (True, "ok")))
    monkeypatch.setattr(EventService, "get_event_participants", staticmethod(lambda eid, status_filter=None: [participant]))
    monkeypatch.setattr(EventService, "create_event_task", staticmethod(lambda eid, uid, body: (True, "ok", task)))
    monkeypatch.setattr(EventService, "get_event_tasks", staticmethod(lambda eid: [task]))
    monkeypatch.setattr(EventService, "submit_task_action", staticmethod(lambda tid, uid, aid: (True, "ok", completion)))
    monkeypatch.setattr(EventService, "get_task_completion_summary", staticmethod(lambda tid, uid: {"done": 1, "total": 1}))
    monkeypatch.setattr(EventService, "get_event", staticmethod(lambda eid, uid: (True, "ok", event)))
    monkeypatch.setattr(EventService, "list_events", staticmethod(lambda uid, filters=None: [event]))
    monkeypatch.setattr(EventService, "get_pending_events", staticmethod(lambda college_id: [event]))

    assert client.post("/api/events/create", headers=auth_headers, json={"event_name": "x", "description": "y", "event_type": "hackathon", "creator_type": "user", "start_time": "2026-01-01T00:00:00+00:00", "end_time": "2026-01-02T00:00:00+00:00"}).status_code == 201
    assert client.post("/api/events/1/submit", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/approve", headers=personnel_auth_headers).status_code == 200
    assert client.post("/api/events/1/reject", headers=personnel_auth_headers, json={"reason": "x"}).status_code == 200
    assert client.post("/api/events/1/cancel", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/complete", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/register", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/confirm-attendance", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/drop", headers=auth_headers).status_code == 200
    assert client.get("/api/events/1/participants", headers=auth_headers).status_code == 200
    assert client.post("/api/events/1/tasks", headers=auth_headers, json={"title": "t", "actions": [{"id": 1, "text": "a", "xp": 1}]}).status_code == 201
    assert client.get("/api/events/1/tasks", headers=auth_headers).status_code == 200
    assert client.post("/api/events/tasks/1/submit-action", headers=auth_headers, json={"action_id": 1}).status_code == 200
    assert client.get("/api/events/tasks/1/summary", headers=auth_headers).status_code == 200
    assert client.get("/api/events/1", headers=auth_headers).status_code == 200
    assert client.get("/api/events/", headers=auth_headers).status_code == 200
    assert client.get("/api/events/pending", headers=personnel_auth_headers).status_code == 200


# -----------------------------------------------------------------------------
# Scoring remaining success contract (profile explicitly 200)
# -----------------------------------------------------------------------------


def test_success_scoring_profile_route(client, app, auth_headers, seeded_user):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.scoring import UserScoring

        existing = UserScoring.query.filter_by(user_id=seeded_user["id"]).first()
        if not existing:
            scoring = UserScoring(
                user_id=seeded_user["id"],
                motivation_score=Decimal("7.50"),
                dominant_roles=["Builder"],
                interest_scores={"Backend Development": 8.0},
                raw_role_scores={"Builder": 8.0},
            )
            _db.session.add(scoring)
            _db.session.commit()

    resp = client.get("/api/scoring/profile", headers=auth_headers)
    assert resp.status_code == 200
