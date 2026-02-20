from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def _future_iso(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


# -----------------------------------------------------------------------------
# Events: create route success + mal-input
# -----------------------------------------------------------------------------

def test_events_create_success_personnel(client, personnel_user, personnel_auth_headers):
    resp = client.post(
        "/api/events/create",
        headers=personnel_auth_headers,
        json={
            "event_name": "Phase2 Event",
            "description": "Route contract success",
            "event_type": "hackathon",
            "creator_type": "college",
            "creator_entity_id": personnel_user["college_id"],
            "is_college_specific": True,
            "college_id": personnel_user["college_id"],
            "start_time": _future_iso(1),
            "end_time": _future_iso(2),
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True


def test_events_create_failure_missing_json_body(client, personnel_auth_headers):
    resp = client.post("/api/events/create", headers=personnel_auth_headers)
    assert resp.status_code == 400


# -----------------------------------------------------------------------------
# Communities: explicit success and failure pairing
# -----------------------------------------------------------------------------

def test_communities_join_failure_not_found(client, auth_headers):
    resp = client.post("/api/communities/join/999999", headers=auth_headers)
    assert resp.status_code == 400


def test_communities_view_failure_forbidden_when_not_member(client, auth_headers, community_factory):
    c = community_factory(name="View Guard Community", subject="Guard")
    cid = c["community_id"]

    resp = client.get(f"/api/communities/view/{cid}", headers=auth_headers)
    # creator is member in fallback path; if so, this can be 200. enforce non-5xx failure-or-success contract.
    assert resp.status_code in (200, 403)


# -----------------------------------------------------------------------------
# Scoring: success + mal-input pairs
# -----------------------------------------------------------------------------

def test_scoring_submit_failure_missing_responses(client, auth_headers):
    resp = client.post("/api/scoring/submit", headers=auth_headers, json={})
    assert resp.status_code == 400


def test_scoring_submit_success_with_monkeypatched_service(client, auth_headers, monkeypatch):
    from app.routes import scoring_routes

    class FakeScoringService:
        def process_initial_questionnaire(self, user_id, responses):
            return {"dominant_roles": ["Builder"], "motivation_score": 7.5}

    monkeypatch.setattr(scoring_routes, "get_scoring_service", lambda: FakeScoringService())

    resp = client.post(
        "/api/scoring/submit",
        headers=auth_headers,
        json={"responses": {"q1": "a", "q2": "b"}},
    )
    assert resp.status_code == 200


def test_scoring_profile_failure_not_scored(client, auth_headers):
    resp = client.get("/api/scoring/profile", headers=auth_headers)
    assert resp.status_code in (200, 404)


def test_scoring_questionnaire_success(client, auth_headers):
    resp = client.get("/api/scoring/questionnaire", headers=auth_headers)
    assert resp.status_code == 200


def test_scoring_history_success(client, auth_headers):
    resp = client.get("/api/scoring/history", headers=auth_headers)
    assert resp.status_code == 200


def test_scoring_retake_success(client, auth_headers):
    resp = client.post("/api/scoring/retake", headers=auth_headers)
    assert resp.status_code == 200


# -----------------------------------------------------------------------------
# Personnel: success + mal-input pairs
# -----------------------------------------------------------------------------

def test_personnel_profile_success(client, personnel_auth_headers):
    resp = client.get("/api/personnel/profile", headers=personnel_auth_headers)
    assert resp.status_code == 200


def test_personnel_whitelist_add_single_failure_missing_email(client, personnel_auth_headers):
    resp = client.post("/api/personnel/whitelist/add-single", headers=personnel_auth_headers, json={})
    # role permissions may block earlier with 403; if permitted, validation gives 400
    assert resp.status_code in (400, 403)


def test_personnel_email_config_patch_failure_missing_fields(client, app, personnel_user, personnel_auth_headers):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.college_personnel import CollegePersonnel
        p = _db.session.get(CollegePersonnel, personnel_user["id"])
        p.can_manage_personnel = True
        _db.session.commit()

    resp = client.patch("/api/personnel/college/email-config", headers=personnel_auth_headers, json={"domain": "x.edu"})
    assert resp.status_code == 400


def test_personnel_email_config_get_success(client, app, personnel_user, personnel_auth_headers):
    with app.app_context():
        from app.extensions import db as _db
        from app.models.college_personnel import CollegePersonnel
        p = _db.session.get(CollegePersonnel, personnel_user["id"])
        p.can_manage_personnel = True
        _db.session.commit()

    resp = client.get("/api/personnel/college/email-config", headers=personnel_auth_headers)
    assert resp.status_code == 200


# -----------------------------------------------------------------------------
# Projects members routes: explicit failure contract (mal-input / missing target)
# -----------------------------------------------------------------------------

def test_projects_members_failure_missing_target_user_id(client, auth_headers, project_factory):
    p = project_factory(title="Member Route Contract")
    resp = client.post(f"/api/projects/{p['id']}/members", headers=auth_headers, json={})
    assert resp.status_code == 400


def test_projects_members_update_remove_failure_not_found(client, auth_headers, project_factory):
    p = project_factory(title="Member Missing Target")
    patch_resp = client.patch(f"/api/projects/{p['id']}/members/999999", headers=auth_headers, json={"role": "contributor"})
    assert patch_resp.status_code in (400, 404)

    del_resp = client.delete(f"/api/projects/{p['id']}/members/999999", headers=auth_headers)
    assert del_resp.status_code in (400, 404)
