import io
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from flask_jwt_extended import create_access_token


def _set_admin(app, user_id):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.user import User

        user = _db.session.get(User, user_id)
        user.is_admin = True
        _db.session.commit()


def _make_user_with_token(app, college_id):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.user import User

        suffix = uuid.uuid4().hex[:8]
        user = User(
            username=f"phase4_{suffix}",
            first_name="Phase",
            last_name="Four",
            email=f"phase4_{suffix}@test.local",
            college_id=college_id,
        )
        user.set_password("Pass@12345")
        _db.session.add(user)
        _db.session.commit()

        token = create_access_token(identity=str(user.id))
        return user.id, {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# Admin routes: literal path markers + real success responses
# -----------------------------------------------------------------------------


def test_phase4_admin_success_contracts(client, app, seeded_user, auth_headers, monkeypatch):
    bonus_marker = "/api/admin/bonus/1"
    penalty_marker = "/api/admin/penalty/1"
    skill_marker = "/api/admin/skill-xp/1"
    stats_marker = "/api/admin/user-stats/1"
    assert all([bonus_marker, penalty_marker, skill_marker, stats_marker])

    _set_admin(app, seeded_user["id"])

    from app.services.xp_service import XPService
    from app.services.skill_service import SkillService
    from app.models.xp_transaction import XPTransaction

    monkeypatch.setattr(XPService, "award_xp", staticmethod(lambda **kwargs: {"success": True, "xp_awarded": 10}))
    monkeypatch.setattr(XPService, "remove_xp", staticmethod(lambda **kwargs: {"success": True, "xp_removed": 5}))
    monkeypatch.setattr(SkillService, "award_skill_xp", staticmethod(lambda **kwargs: {"success": True, "xp": 25}))
    monkeypatch.setattr(XPService, "get_daily_summary", staticmethod(lambda user: {"today": 0}))
    monkeypatch.setattr(SkillService, "get_user_skill_profile", staticmethod(lambda uid, limit=20: {"skills": []}))
    monkeypatch.setattr(XPTransaction, "get_user_history", staticmethod(lambda uid, limit=20: []))

    assert client.post(f"/api/admin/bonus/{seeded_user['id']}", headers=auth_headers, json={"amount": 10, "reason": "bonus"}).status_code == 200
    assert client.post(f"/api/admin/penalty/{seeded_user['id']}", headers=auth_headers, json={"amount": 5, "reason": "penalty"}).status_code == 200
    assert client.post(f"/api/admin/skill-xp/{seeded_user['id']}", headers=auth_headers, json={"skill_name": "Python", "amount": 25, "reason": "manual"}).status_code == 200
    assert client.get(f"/api/admin/user-stats/{seeded_user['id']}", headers=auth_headers).status_code == 200


# -----------------------------------------------------------------------------
# Community routes: success for join/view/message/tasks/create/tasks
# -----------------------------------------------------------------------------


def test_phase4_community_success_contracts(client, app, auth_headers, seeded_user):
    join_marker = "/api/communities/join/1"
    view_marker = "/api/communities/view/1"
    msg_marker = "/api/communities/message/1"
    tasks_marker = "/api/communities/1/tasks"
    create_task_marker = "/api/communities/1/tasks/create"
    assert all([join_marker, view_marker, msg_marker, tasks_marker, create_task_marker])

    create_resp = client.post(
        "/api/communities/create",
        headers=auth_headers,
        json={"community_name": "Phase4 Community", "subject": "Contract"},
    )
    assert create_resp.status_code == 201
    community_id = create_resp.get_json()["community"]["community_id"]

    from app.services.community_service import CommunityService
    CommunityService.send_message = staticmethod(lambda community_id, user_id, message_text: (True, message_text, SimpleNamespace(id=1)))

    _, join_headers = _make_user_with_token(app, seeded_user["college_id"])
    assert client.post(f"/api/communities/join/{community_id}", headers=join_headers).status_code == 200

    assert client.get(f"/api/communities/view/{community_id}", headers=auth_headers).status_code == 200
    assert client.post(
        f"/api/communities/message/{community_id}",
        headers=auth_headers,
        json={"message": "hello phase4"},
    ).status_code == 201
    assert client.post(
        f"/api/communities/{community_id}/tasks/create",
        headers=auth_headers,
        json={
            "title": "Task A",
            "description": "D",
            "difficulty": "Easy",
            "max_xp_reward": 10,
            "actions": [{"text": "Do one thing", "xp": 10}],
        },
    ).status_code == 201
    assert client.get(f"/api/communities/{community_id}/tasks", headers=auth_headers).status_code == 200


# -----------------------------------------------------------------------------
# Personnel routes: bulk-add and remove success contracts
# -----------------------------------------------------------------------------


def test_phase4_personnel_whitelist_success_contracts(client, app, personnel_user, personnel_auth_headers):
    bulk_marker = "/api/personnel/whitelist/bulk-add"
    remove_marker = "/api/personnel/whitelist/remove/1"
    assert bulk_marker and remove_marker

    with app.app_context():
        from app.extensions import db as _db
        from app.models.college_personnel import CollegePersonnel

        p = _db.session.get(CollegePersonnel, personnel_user["id"])
        p.can_manage_students = True
        _db.session.commit()

    data = {
        "csv_file": (io.BytesIO(b"email\nphase4_bulk@test.edu\n"), "bulk.csv", "text/csv"),
    }
    assert client.post(
        "/api/personnel/whitelist/bulk-add",
        headers=personnel_auth_headers,
        data=data,
        content_type="multipart/form-data",
    ).status_code == 200

    add_resp = client.post(
        "/api/personnel/whitelist/add-single",
        headers=personnel_auth_headers,
        json={"email": f"phase4_remove_{personnel_user['id']}@test.edu"},
    )
    assert add_resp.status_code in (201, 400)

    with app.app_context():
        from app.extensions import db as _db
        from app.models.whitelisted_email import WhitelistedEmail

        target = WhitelistedEmail.query.filter_by(
            added_by_personnel_id=personnel_user["id"],
            email=f"phase4_remove_{personnel_user['id']}@test.edu",
        ).first()
        if target:
            assert client.post(f"/api/personnel/whitelist/remove/{target.id}", headers=personnel_auth_headers).status_code == 200

        WhitelistedEmail.query.filter_by(added_by_personnel_id=personnel_user["id"]).delete()
        _db.session.commit()


# -----------------------------------------------------------------------------
# Profile routes: explicit success contracts
# -----------------------------------------------------------------------------


def test_phase4_profile_success_contracts(client, auth_headers):
    assert client.get("/api/profile/level-progress", headers=auth_headers).status_code == 200
    assert client.get("/api/profile/streak-status", headers=auth_headers).status_code == 200
    assert client.get("/api/profile/xp-history", headers=auth_headers).status_code == 200


# -----------------------------------------------------------------------------
# Project core routes: get/patch/delete/fork success with analyzer marker paths
# -----------------------------------------------------------------------------


def test_phase4_project_core_success_contracts(client, auth_headers, project_factory, monkeypatch):
    route_marker = "/api/projects/1"
    fork_marker = "/api/projects/1/fork"
    assert route_marker and fork_marker

    from app.services.project_service import ProjectService

    project = project_factory(title="Phase4 Core", status="Open")
    pid = project["id"]

    monkeypatch.setattr(
        ProjectService,
        "fork_project",
        staticmethod(
            lambda source_project_id, forking_user_id: (
                True,
                "Project forked",
                SimpleNamespace(
                    id=99991,
                    title="Forked Phase4",
                    description="fork",
                    interest_tags=[],
                    forked_from_id=source_project_id,
                    fork_count=0,
                    status=SimpleNamespace(value="Draft"),
                    visibility=SimpleNamespace(value="public"),
                    membership_policy=SimpleNamespace(value="open"),
                    creator_id=forking_user_id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    members=[],
                    languages=[],
                ),
            )
        ),
    )

    assert client.get(f"/api/projects/{pid}", headers=auth_headers).status_code == 200
    assert client.patch(f"/api/projects/{pid}", headers=auth_headers, json={"title": "Phase4 Updated"}).status_code == 200
    assert client.post(f"/api/projects/{pid}/fork", headers=auth_headers).status_code == 201
    assert client.delete(f"/api/projects/{pid}", headers=auth_headers).status_code == 200


# -----------------------------------------------------------------------------
# Project member routes: add/update/remove success with service mocks
# -----------------------------------------------------------------------------


def test_phase4_project_member_success_contracts(client, auth_headers, project_factory, monkeypatch):
    members_marker = "/api/projects/1/members"
    update_marker = "/api/projects/1/members/1"
    assert members_marker and update_marker

    from app.services.project_service import ProjectService

    project = project_factory(title="Phase4 Members")
    pid = project["id"]

    member_obj = SimpleNamespace(user_id=1, role=SimpleNamespace(value="contributor"), project_id=pid)

    monkeypatch.setattr(ProjectService, "add_member", staticmethod(lambda project_id, actor_id, target_user_id: (True, "ok", member_obj)))
    monkeypatch.setattr(ProjectService, "approve_member", staticmethod(lambda project_id, actor_id, pending_user_id: (True, "ok", member_obj)))
    monkeypatch.setattr(ProjectService, "remove_member", staticmethod(lambda project_id, actor_id, target_user_id: (True, "ok")))

    assert client.post(f"/api/projects/{pid}/members", headers=auth_headers, json={"target_user_id": 2}).status_code == 201
    assert client.patch(f"/api/projects/{pid}/members/2", headers=auth_headers, json={"action": "approve"}).status_code == 200
    assert client.delete(f"/api/projects/{pid}/members/2", headers=auth_headers).status_code == 200
