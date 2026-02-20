"""
Event Routes — JSON API

All routes return JSON. No Jinja2, no redirects, no flash().
Auth: JWT Bearer token (header-based, JWT_TOKEN_LOCATION = ['headers']).

Caller types:
- Student:   JWT identity is a plain integer string e.g. "42"
- Personnel: JWT identity is prefixed string e.g. "personnel_7"

Helpers:
- get_user_id_or_error()      → (user_id, None) | (None, (response, 401/403))
- get_personnel_id_or_error() → (personnel_id, None) | (None, (response, 401/403))

Dual-caller routes (cancel, complete):
- Identity type is resolved by inspecting the raw JWT identity string prefix.
- Personnel identity starts with "personnel_". Student identity does not.
- Branch is explicit — no try/except flow control.

Service return patterns (varies by method — see comments per route):
- (bool, str, object|None)  — most lifecycle and participation methods
- (bool, str)               — drop, cancel, complete, reject
- list                      — list_events, get_event_participants,
                              get_event_tasks, get_pending_events
- dict|None                 — get_task_completion_summary

Architecture: routes → services → models
No business logic here. Serialization helpers at bottom of file (presentation concern).
"""

import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.services.event_service import EventService
from app.models.college_personnel import CollegePersonnel
from app.utils.jwt_helpers import get_user_id_or_error, get_personnel_id_or_error

logger = logging.getLogger(__name__)

events_bp = Blueprint("events", __name__)


# ===========================================================================
# GROUP 1 — EVENT LIFECYCLE
# ===========================================================================

@events_bp.route("/create", methods=["POST"])
@jwt_required()
def create_event():
    """
    POST /api/events/create

    Dual caller: student OR personnel.
    - Personnel: creator_type forced to EventCreatorType.COLLEGE by the service
      when caller is personnel. Route passes creator_type from body but personnel
      callers should always send creator_type="college".
    - Student: must be >= MIN_LEVEL_TO_CREATE_EVENT (enforced in service).

    Body: see EventService.create_event() docstring for full data dict.
    """
    identity = get_jwt_identity()
    identity_str = str(identity) if identity else ""

    if identity_str.startswith("personnel_"):
        personnel_id, err = get_personnel_id_or_error()
        if err:
            return err
        caller_id = personnel_id
    else:
        user_id, err = get_user_id_or_error()
        if err:
            return err
        caller_id = user_id

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    success, message, event = EventService.create_event(caller_id, body)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_event(event)
    }), 201


@events_bp.route("/<int:event_id>/submit", methods=["POST"])
@jwt_required()
def submit_event_for_approval(event_id):
    """
    POST /api/events/<event_id>/submit

    Student or personnel. Must be the event creator.
    Transitions DRAFT → PENDING (or ACTIVE for college-created events).
    """
    user_id, user_err = get_user_id_or_error()
    personnel_id, personnel_err = get_personnel_id_or_error()

    if user_id is None and personnel_id is None:
        return user_err  # 401 from missing token

    caller_id = user_id if user_id is not None else personnel_id
    caller_is_personnel = personnel_id is not None

    success, message, event = EventService.submit_event_for_approval(
        event_id, caller_id, caller_is_personnel
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_event(event)
    }), 200


@events_bp.route("/<int:event_id>/approve", methods=["POST"])
@jwt_required()
def approve_event(event_id):
    """
    POST /api/events/<event_id>/approve

    Personnel only. College authority must match event's college.
    Transitions PENDING → ACTIVE.
    """
    personnel_id, err = get_personnel_id_or_error()
    if err:
        return err

    personnel = db.session.get(CollegePersonnel, personnel_id)
    if not personnel:
        return jsonify({'error': 'Personnel not found'}), 404

    success, message, event = EventService.approve_event(event_id, personnel.college_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_event(event)
    }), 200


@events_bp.route("/<int:event_id>/reject", methods=["POST"])
@jwt_required()
def reject_event(event_id):
    """
    POST /api/events/<event_id>/reject

    Personnel only. College authority must match event's college.
    Transitions PENDING → CANCELLED.

    Body: { "reason": str }  — required.

    Returns (bool, str) — no data object.
    """
    personnel_id, err = get_personnel_id_or_error()
    if err:
        return err

    personnel = db.session.get(CollegePersonnel, personnel_id)
    if not personnel:
        return jsonify({'error': 'Personnel not found'}), 404

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    reason = body.get("reason", "").strip()
    if not reason:
        return jsonify({"success": False, "message": "A rejection reason is required"}), 400

    success, message = EventService.reject_event(event_id, personnel.college_id, reason)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200


@events_bp.route("/<int:event_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_event(event_id):
    """
    POST /api/events/<event_id>/cancel

    Dual caller: student OR personnel.
    - Student: can cancel only their own event, from DRAFT or ACTIVE.
    - Personnel: can cancel any non-terminal event for their college.

    Caller type resolved by JWT identity prefix — explicit branch, no exception flow.
    Returns (bool, str) — no data object.
    """
    identity = get_jwt_identity()
    identity_str = str(identity) if identity else ""

    if identity_str.startswith("personnel_"):
        personnel_id, err = get_personnel_id_or_error()
        if err:
            return err
        personnel = db.session.get(CollegePersonnel, personnel_id)
        if not personnel:
            return jsonify({'error': 'Personnel not found'}), 404
        success, message = EventService.cancel_event(
            event_id, authority_college_id=personnel.college_id
        )
    else:
        user_id, err = get_user_id_or_error()
        if err:
            return err
        success, message = EventService.cancel_event(event_id, user_id=user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200


@events_bp.route("/<int:event_id>/complete", methods=["POST"])
@jwt_required()
def complete_event(event_id):
    """
    POST /api/events/<event_id>/complete

    Dual caller: student OR personnel.
    - Student: must be the event creator.
    - Personnel: must match event's college.

    Caller type resolved by JWT identity prefix — explicit branch, no exception flow.
    Returns (bool, str) — no data object.
    """
    identity = get_jwt_identity()
    identity_str = str(identity) if identity else ""

    if identity_str.startswith("personnel_"):
        personnel_id, err = get_personnel_id_or_error()
        if err:
            return err
        personnel = db.session.get(CollegePersonnel, personnel_id)
        if not personnel:
            return jsonify({'error': 'Personnel not found'}), 404
        success, message = EventService.complete_event(
            event_id, authority_college_id=personnel.college_id
        )
    else:
        user_id, err = get_user_id_or_error()
        if err:
            return err
        success, message = EventService.complete_event(event_id, user_id=user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200


# ===========================================================================
# GROUP 2 — PARTICIPATION
# ===========================================================================

@events_bp.route("/<int:event_id>/register", methods=["POST"])
@jwt_required()
def register_for_event(event_id):
    """
    POST /api/events/<event_id>/register

    Student only.
    Returns (bool, str, EventParticipant|None).
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    success, message, participant = EventService.register_for_event(event_id, user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_participant(participant)
    }), 200


@events_bp.route("/<int:event_id>/confirm-attendance", methods=["POST"])
@jwt_required()
def confirm_attendance(event_id):
    """
    POST /api/events/<event_id>/confirm-attendance

    Student only. Self-reported within CHECK_IN_WINDOW_HOURS of event start.
    Returns (bool, str, EventParticipant|None).
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    success, message, participant = EventService.confirm_attendance(event_id, user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_participant(participant)
    }), 200


@events_bp.route("/<int:event_id>/drop", methods=["POST"])
@jwt_required()
def drop_from_event(event_id):
    """
    POST /api/events/<event_id>/drop

    Student only.
    Returns (bool, str) — no data object.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    success, message = EventService.drop_from_event(event_id, user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200


@events_bp.route("/<int:event_id>/participants", methods=["GET"])
@jwt_required()
def get_event_participants(event_id):
    """
    GET /api/events/<event_id>/participants?status=<ParticipantStatus>

    Student only. Optional query param: status (filters by ParticipantStatus).
    Returns list[EventParticipant] directly — no (bool, str) wrapper.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    status_filter = request.args.get("status")
    participants = EventService.get_event_participants(event_id, status_filter)

    return jsonify({
        "success": True,
        "data": [_serialize_participant(p) for p in participants],
        "count": len(participants)
    }), 200


# ===========================================================================
# GROUP 3 — EVENT TASKS
# ===========================================================================

@events_bp.route("/<int:event_id>/tasks", methods=["POST"])
@jwt_required()
def create_event_task(event_id):
    """
    POST /api/events/<event_id>/tasks

    Student only. Must be the event creator.
    Body: { title, description, difficulty, xp_reward, actions, is_required }
    Returns (bool, str, EventTask|None).
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    success, message, task = EventService.create_event_task(event_id, user_id, body)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_task(task)
    }), 201


@events_bp.route("/<int:event_id>/tasks", methods=["GET"])
@jwt_required()
def get_event_tasks(event_id):
    """
    GET /api/events/<event_id>/tasks

    Student only.
    Returns list[EventTask] directly — no (bool, str) wrapper.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    tasks = EventService.get_event_tasks(event_id)

    return jsonify({
        "success": True,
        "data": [_serialize_task(t) for t in tasks],
        "count": len(tasks)
    }), 200


@events_bp.route("/tasks/<int:task_id>/submit-action", methods=["POST"])
@jwt_required()
def submit_task_action(task_id):
    """
    POST /api/events/tasks/<task_id>/submit-action

    Student only. User must be a CONFIRMED participant of the event.
    Body: { "action_id": int }
    Returns (bool, str, EventTaskCompletion|None).
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON"}), 400

    action_id = body.get("action_id")
    if action_id is None or not isinstance(action_id, int):
        return jsonify({"success": False, "message": "action_id must be an integer"}), 400

    success, message, completion = EventService.submit_task_action(task_id, user_id, action_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_completion(completion)
    }), 200


@events_bp.route("/tasks/<int:task_id>/summary", methods=["GET"])
@jwt_required()
def get_task_completion_summary(task_id):
    """
    GET /api/events/tasks/<task_id>/summary

    Student only.
    Returns dict|None directly — no (bool, str) wrapper.
    None means task not found → 404.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    summary = EventService.get_task_completion_summary(task_id, user_id)

    if summary is None:
        return jsonify({"success": False, "message": "Task not found"}), 404

    return jsonify({
        "success": True,
        "data": summary
    }), 200


# ===========================================================================
# GROUP 4 — DISCOVERY AND QUERIES
# ===========================================================================

@events_bp.route("/<int:event_id>", methods=["GET"])
@jwt_required()
def get_event(event_id):
    """
    GET /api/events/<event_id>

    Student only. College-specific events restricted to matching college.
    Returns (bool, str, Event|None).
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    success, message, event = EventService.get_event(event_id, user_id)

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": _serialize_event(event)
    }), 200


@events_bp.route("/", methods=["GET"], strict_slashes=False)
@jwt_required()
def list_events():
    """
    GET /api/events/?event_type=<str>

    Student only. Returns active events visible to the user's college.
    Optional query param: event_type.
    Returns list[Event] directly — no (bool, str) wrapper.
    """
    user_id, err = get_user_id_or_error()
    if err:
        return err

    filters = {}
    event_type = request.args.get("event_type")
    if event_type:
        filters["event_type"] = event_type

    events = EventService.list_events(user_id, filters or None)

    return jsonify({
        "success": True,
        "data": [_serialize_event(e) for e in events],
        "count": len(events)
    }), 200


# ===========================================================================
# GROUP 5 — AUTHORITY QUERIES
# ===========================================================================

@events_bp.route("/pending", methods=["GET"])
@jwt_required()
def get_pending_events():
    """
    GET /api/events/pending

    Personnel only. Returns pending events for the authority's college.
    Returns list[Event] directly — no (bool, str) wrapper.
    """
    personnel_id, err = get_personnel_id_or_error()
    if err:
        return err

    personnel = db.session.get(CollegePersonnel, personnel_id)
    if not personnel:
        return jsonify({'error': 'Personnel not found'}), 404

    events = EventService.get_pending_events(personnel.college_id)

    return jsonify({
        "success": True,
        "data": [_serialize_event(e) for e in events],
        "count": len(events)
    }), 200


# ===========================================================================
# PRIVATE SERIALIZERS — presentation concern, lives in routes layer
# ===========================================================================

def _serialize_event(event):
    """Minimal serialization for Event model instances."""
    if event is None:
        return None
    return {
        "event_id": event.event_id,
        "event_name": event.event_name,
        "description": event.description,
        "event_type": event.event_type,
        "status": event.status,
        "creator_type": event.creator_type,
        "creator_entity_id": event.creator_entity_id,
        "created_by": event.created_by,
        "is_college_specific": event.is_college_specific,
        "college_id": event.college_id,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "registration_deadline": (
            event.registration_deadline.isoformat()
            if event.registration_deadline else None
        ),
        "max_participants": event.max_participants,
        "programming_languages": event.programming_languages,
        "requirements": event.requirements,
        "completion_xp": event.completion_xp,
        "is_verified": event.is_verified,
        "verified_at": event.verified_at.isoformat() if event.verified_at else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
    }


def _serialize_participant(participant):
    """Minimal serialization for EventParticipant model instances."""
    if participant is None:
        return None
    return {
        "participant_id": participant.id,
        "event_id": participant.event_id,
        "user_id": participant.user_id,
        "registration_status": participant.registration_status,
        "registered_at": (
            participant.registered_at.isoformat()
            if participant.registered_at else None
        ),
        "completed_at": (
            participant.completed_at.isoformat()
            if participant.completed_at else None
        ),
    }


def _serialize_task(task):
    """Minimal serialization for EventTask model instances."""
    if task is None:
        return None
    return {
        "task_id": task.task_id,
        "event_id": task.event_id,
        "title": task.title,
        "description": task.description,
        "difficulty": task.difficulty,
        "xp_reward": task.xp_reward,
        "actions": task.actions,
        "is_required": task.is_required,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def _serialize_completion(completion):
    """Minimal serialization for EventTaskCompletion model instances."""
    if completion is None:
        return None
    return {
        "completion_id": completion.id,
        "event_task_id": completion.event_task_id,
        "user_id": completion.user_id,
        "action_id": completion.action_id,
        "status": completion.status,
        "xp_awarded": completion.xp_awarded,
        "submitted_at": (
            completion.submitted_at.isoformat()
            if completion.submitted_at else None
        ),
        "reviewed_at": (
            completion.reviewed_at.isoformat()
            if completion.reviewed_at else None
        ),
    }
