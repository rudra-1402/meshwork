"""
Tests for event lifecycle, dual-caller identity, and state machine transitions.

Coverage targets:
  - Personnel creates event → created_by_personnel_id set, created_by null
  - Personnel submits/publishes their event (dual-caller submit path)
  - Student creates event → created_by_user_id set
  - Invalid transition (DRAFT → COMPLETED) returns error
  - College authority approve/reject scoped to personnel.college_id
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future_iso(days=7):
    """Return an ISO 8601 datetime string N days from now."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _event_body(**overrides):
    base = {
        "event_name": "Test Event",
        "description": "A test event description that is long enough",
        "event_type": "hackathon",
        "creator_type": "college",
        "start_time": _future_iso(1),
        "end_time": _future_iso(2),
        "is_college_specific": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# D1/D2: Event identity model tests
# ---------------------------------------------------------------------------

class TestEventIdentityModel:

    def test_personnel_creates_event_sets_personnel_fk(self, app, personnel_user):
        """Personnel event creation should set created_by_personnel_id and leave created_by null."""
        with app.app_context():
            from app.services.event_service import EventService
            from app.constants.event_constants import EventCreatorType

            data = _event_body(
                creator_type=EventCreatorType.COLLEGE,
                college_id=personnel_user["college_id"],
                creator_entity_id=personnel_user["college_id"],
            )
            success, msg, event = EventService.create_event(personnel_user["id"], data)

            assert success, msg
            assert event.created_by is None
            assert event.created_by_personnel_id == personnel_user["id"]
            assert event.created_by_user_id is None

            # Cleanup
            from app.extensions import db as _db
            _db.session.delete(event)
            _db.session.commit()

    def test_student_creates_event_sets_user_fk(self, app, seeded_user):
        """Student event creation should set created_by_user_id and created_by."""
        with app.app_context():
            from app.services.event_service import EventService
            from app.models.user import User
            from app.extensions import db as _db
            from app.constants.event_constants import EventCreatorType

            # Bump level high enough to pass the gate
            user = _db.session.get(User, seeded_user["id"])
            original_level = user.level
            user.level = 200
            user.xp = 200 * 200 * 100
            _db.session.commit()

            try:
                data = _event_body(
                    creator_type=EventCreatorType.USER,
                    college_id=seeded_user["college_id"],
                )
                success, msg, event = EventService.create_event(seeded_user["id"], data)

                assert success, msg
                assert event.created_by == seeded_user["id"]
                assert event.created_by_user_id == seeded_user["id"]
                assert event.created_by_personnel_id is None

                _db.session.delete(event)
            finally:
                user = _db.session.get(User, seeded_user["id"])
                user.level = original_level
                user.xp = 0
                _db.session.commit()


# ---------------------------------------------------------------------------
# D3: Dual-caller submit route
# ---------------------------------------------------------------------------

class TestEventSubmitDualCaller:

    def test_personnel_can_submit_their_event(self, client, personnel_user, personnel_auth_headers):
        """POST /api/events/<id>/submit should work for personnel JWT."""
        with client.application.app_context():
            from app.services.event_service import EventService
            from app.constants.event_constants import EventCreatorType
            from app.extensions import db as _db

            data = _event_body(
                creator_type=EventCreatorType.COLLEGE,
                college_id=personnel_user["college_id"],
                creator_entity_id=personnel_user["college_id"],
            )
            success, msg, event = EventService.create_event(personnel_user["id"], data)
            assert success, msg
            event_id = event.event_id
            _db.session.expunge(event)

        resp = client.post(
            f"/api/events/{event_id}/submit",
            headers=personnel_auth_headers,
        )
        assert resp.status_code == 200, resp.get_json()
        data = resp.get_json()
        assert data["success"] is True
        # College-type events go directly to active
        assert data["data"]["status"] == "active"

        # Cleanup
        with client.application.app_context():
            from app.models.event_models import Event
            from app.extensions import db as _db
            ev = _db.session.get(Event, event_id)
            if ev:
                _db.session.delete(ev)
            _db.session.commit()

    def test_submit_requires_auth(self, client):
        """POST /api/events/<id>/submit with no token returns 401."""
        resp = client.post("/api/events/9999/submit")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# E: State machine — invalid transition
# ---------------------------------------------------------------------------

class TestEventStateMachine:

    def test_can_transition_valid(self):
        """can_transition should return True for valid transitions."""
        from app.services.event_service import EventService
        from app.constants.event_constants import EventStatus
        assert EventService.can_transition(EventStatus.DRAFT, EventStatus.PENDING) is True
        assert EventService.can_transition(EventStatus.PENDING, EventStatus.ACTIVE) is True
        assert EventService.can_transition(EventStatus.ACTIVE, EventStatus.COMPLETED) is True

    def test_can_transition_invalid(self):
        """can_transition should return False for skipped/terminal transitions."""
        from app.services.event_service import EventService
        from app.constants.event_constants import EventStatus
        assert EventService.can_transition(EventStatus.DRAFT, EventStatus.COMPLETED) is False
        assert EventService.can_transition(EventStatus.COMPLETED, EventStatus.ACTIVE) is False
        assert EventService.can_transition(EventStatus.CANCELLED, EventStatus.PENDING) is False

    def test_submit_active_event_rejected(self, app, personnel_user):
        """Cannot submit an already-active event (DRAFT→ACTIVE then re-submit)."""
        with app.app_context():
            from app.services.event_service import EventService
            from app.constants.event_constants import EventCreatorType
            from app.extensions import db as _db

            data = _event_body(
                creator_type=EventCreatorType.COLLEGE,
                college_id=personnel_user["college_id"],
                creator_entity_id=personnel_user["college_id"],
            )
            success, msg, event = EventService.create_event(personnel_user["id"], data)
            assert success

            # First submit → goes active (college type)
            success, msg, event = EventService.submit_event_for_approval(
                event.event_id, personnel_user["id"], caller_is_personnel=True
            )
            assert success
            assert event.status == "active"

            # Second submit → should fail (active cannot go to pending/active again)
            success2, msg2, _ = EventService.submit_event_for_approval(
                event.event_id, personnel_user["id"], caller_is_personnel=True
            )
            assert success2 is False
            assert "cannot transition" in msg2.lower()

            _db.session.delete(event)
            _db.session.commit()


# ---------------------------------------------------------------------------
# C: Whitelist scoped to college_id
# ---------------------------------------------------------------------------

class TestWhitelistMultiTenant:

    def test_check_if_whitelisted_is_college_scoped(self, app, personnel_user):
        """check_if_whitelisted returns False for correct email but wrong college."""
        with app.app_context():
            from app.services.whitelist_service import WhitelistService

            # Add to personnel's college
            success, _, entry = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email=f"scoped_{uuid.uuid4().hex[:6]}@test.edu",
                added_by_personnel_id=personnel_user["id"],
            )
            assert success

            # Wrong college_id → should not find it
            whitelisted, found = WhitelistService.check_if_whitelisted(
                entry.email, college_id=personnel_user["college_id"] + 9999
            )
            assert whitelisted is False
            assert found is None

            # Correct college_id → should find it
            whitelisted2, found2 = WhitelistService.check_if_whitelisted(
                entry.email, college_id=personnel_user["college_id"]
            )
            assert whitelisted2 is True
            assert found2 is not None

            # Cleanup
            from app.models.whitelisted_email import WhitelistedEmail
            from app.extensions import db as _db
            WhitelistedEmail.query.filter_by(id=entry.id).delete()
            _db.session.commit()
