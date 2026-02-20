"""
Event Service — Groups 1 & 2

Business logic for event lifecycle and participation.
Groups 3–5 (tasks, discovery, authority queries) follow below.

Architecture:
- ALL business logic lives here. Routes do not decide outcomes.
- Models are schema only. No business logic called on model instances.
- XP awards are always non-fatal — failures log a warning and never
  roll back a legitimate user action.
- State transitions are enforced via VALID_EVENT_TRANSITIONS and
  VALID_PARTICIPANT_TRANSITIONS. No ad-hoc string comparisons.

Dependency direction: routes → this service → models
"""

import logging
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models.event_models import Event, EventParticipant, EventTask, EventTaskCompletion
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.language import Language
from app.services.xp_service import XPService
from app.constants.gamification import XP_AMOUNTS
from app.constants.event_constants import (
    EventStatus,
    EventCreatorType,
    ParticipantStatus,
    TaskCompletionStatus,
    VALID_EVENT_TRANSITIONS,
    VALID_PARTICIPANT_TRANSITIONS,
    MIN_LEVEL_TO_CREATE_EVENT,
    CHECK_IN_WINDOW_HOURS,
    VALID_TASK_DIFFICULTIES,
)

logger = logging.getLogger(__name__)


class EventService:

    @staticmethod
    def can_transition(current_status, target_status):
        """Return True if the given status transition is permitted by the state machine."""
        return target_status in VALID_EVENT_TRANSITIONS.get(current_status, [])

    @staticmethod
    def _is_event_creator(event, caller_id, caller_is_personnel=False):
        """Check whether caller is the original creator of the event."""
        if caller_is_personnel:
            return event.created_by_personnel_id == caller_id
        return (
            event.created_by_user_id == caller_id
            or event.created_by == caller_id  # backward compat for old rows
        )

    # ===========================================================================
    # GROUP 1 — EVENT LIFECYCLE
    # ===========================================================================

    @staticmethod
    def create_event(creator_id, data):
        """
        Create a new event in DRAFT status.

        Permission gates:
        - College authority: no level gate (caller passes creator_type=EventCreatorType.COLLEGE)
        - Community leader or regular user: must be >= MIN_LEVEL_TO_CREATE_EVENT

        The route is responsible for resolving which creator_type applies
        based on the JWT identity before calling this method.

        Args:
            creator_id (int): user.id of the creator (for college authority,
                              this is the personnel id stored in created_by)
            data (dict): {
                event_name, description, event_type,
                creator_type,                   # EventCreatorType constant
                creator_entity_id (optional),   # community_id or college_id
                is_college_specific (bool),
                college_id (optional),
                start_time (ISO str),
                end_time (ISO str),
                registration_deadline (ISO str, optional),
                max_participants (int, optional),
                programming_languages (list, optional),
                requirements (dict, optional),
                completion_xp (int, optional),
            }

        Returns:
            (bool, str, Event|None)
        """
        creator_type = data.get("creator_type")
        if creator_type not in (
            EventCreatorType.COLLEGE,
            EventCreatorType.COMMUNITY,
            EventCreatorType.USER,
        ):
            return False, "Invalid creator type", None

        # Level gate — exempt college authority
        if creator_type != EventCreatorType.COLLEGE:
            user = db.session.get(User, creator_id)
            if not user:
                return False, "User not found", None
            if user.level < MIN_LEVEL_TO_CREATE_EVENT:
                return (
                    False,
                    f"You must be level {MIN_LEVEL_TO_CREATE_EVENT} to create events "
                    f"(you are level {user.level})",
                    None,
                )

        # Required field validation
        required = ["event_name", "description", "event_type", "start_time", "end_time"]
        for field in required:
            if not data.get(field):
                return False, f"Missing required field: {field}", None

        # Parse datetimes
        try:
            start_time = datetime.fromisoformat(data["start_time"])
            end_time = datetime.fromisoformat(data["end_time"])
        except (ValueError, TypeError):
            return False, "Invalid datetime format. Use ISO 8601.", None

        if end_time <= start_time:
            return False, "end_time must be after start_time", None

        registration_deadline = None
        if data.get("registration_deadline"):
            try:
                registration_deadline = datetime.fromisoformat(data["registration_deadline"])
            except (ValueError, TypeError):
                return False, "Invalid registration_deadline format. Use ISO 8601.", None

        try:
            # Populate dual-identity fields
            is_personnel_creator = (creator_type == EventCreatorType.COLLEGE)
            event = Event(
                event_name=data["event_name"].strip(),
                description=data["description"].strip(),
                event_type=data["event_type"].strip(),
                # Legacy field: set for user/community creators, null for personnel
                created_by=None if is_personnel_creator else creator_id,
                created_by_user_id=None if is_personnel_creator else creator_id,
                created_by_personnel_id=creator_id if is_personnel_creator else None,
                creator_type=creator_type,
                creator_entity_id=data.get("creator_entity_id"),
                is_college_specific=bool(data.get("is_college_specific", False)),
                college_id=data.get("college_id"),
                start_time=start_time,
                end_time=end_time,
                registration_deadline=registration_deadline,
                max_participants=data.get("max_participants"),
                programming_languages=data.get("programming_languages", []),
                requirements=data.get("requirements"),
                completion_xp=int(data.get("completion_xp", 0)),
                status=EventStatus.DRAFT,
            )
            db.session.add(event)
            db.session.commit()
            logger.info(
                f"Event created: event_id={event.event_id} by creator_id={creator_id} "
                f"creator_type={creator_type}"
            )
            return True, "Event created successfully", event
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create event for creator_id={creator_id}: {e}")
            return False, "Failed to create event", None

    @staticmethod
    def submit_event_for_approval(event_id, caller_id, caller_is_personnel=False):
        """
        Transition event from DRAFT to PENDING (or ACTIVE for college creators).

        College-created events skip PENDING and go directly to ACTIVE.
        Only the event creator can submit their own event.

        Args:
            event_id (int)
            caller_id (int): user.id or personnel.id of the submitter
            caller_is_personnel (bool): True when caller is a CollegePersonnel

        Returns:
            (bool, str, Event|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        if not EventService._is_event_creator(event, caller_id, caller_is_personnel):
            return False, "Only the event creator can submit for approval", None

        target_status = EventStatus.ACTIVE if event.creator_type == EventCreatorType.COLLEGE else EventStatus.PENDING
        if not EventService.can_transition(event.status, target_status):
            return False, f"Cannot transition from {event.status} to {target_status} (only draft events can be submitted)", None

        try:
            if event.creator_type == EventCreatorType.COLLEGE:
                # College-created events are trusted — skip pending, go active directly
                event.status = EventStatus.ACTIVE
                event.is_verified = True
                event.verified_at = datetime.now(timezone.utc)
                message = "Event published and set to active"
            else:
                event.status = EventStatus.PENDING
                message = "Event submitted for college approval"

            event.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(
                f"Event submitted: event_id={event_id} new_status={event.status} "
                f"by caller_id={caller_id} personnel={caller_is_personnel}"
            )
            return True, message, event
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit event_id={event_id} for approval: {e}")
            return False, "Failed to submit event", None

    @staticmethod
    def approve_event(event_id, authority_college_id):
        """
        Approve a pending event. Transitions PENDING → ACTIVE.

        Only a college authority whose college_id matches event.college_id
        can approve. This method receives the college_id extracted from
        the college authority's JWT by the route.

        TODO: Notify event creator on approval (notification system not yet built).

        Args:
            event_id (int)
            authority_college_id (int): college_id from the authority's JWT

        Returns:
            (bool, str, Event|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        if not EventService.can_transition(event.status, EventStatus.ACTIVE):
            return False, f"Cannot transition from {event.status} to active (only pending events can be approved)", None

        if event.college_id != authority_college_id:
            return False, "You do not have authority over this event's college", None

        try:
            event.status = EventStatus.ACTIVE
            event.is_verified = True
            event.verified_at = datetime.now(timezone.utc)
            event.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(
                f"Event approved: event_id={event_id} by college_id={authority_college_id}"
            )
            # TODO: Notify event creator (notification system not yet implemented)
            return True, "Event approved and set to active", event
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to approve event_id={event_id} for college_id={authority_college_id}: {e}"
            )
            return False, "Failed to approve event", None

    @staticmethod
    def reject_event(event_id, authority_college_id, reason):
        """
        Reject a pending event. Transitions PENDING → CANCELLED.

        Only a college authority whose college_id matches event.college_id
        can reject.

        TODO: Notify event creator with rejection reason (notification system not yet built).

        Args:
            event_id (int)
            authority_college_id (int): college_id from the authority's JWT
            reason (str): rejection reason, logged and stored for future notification

        Returns:
            (bool, str)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found"

        if not EventService.can_transition(event.status, EventStatus.CANCELLED):
            return False, f"Cannot transition from {event.status} to cancelled (only pending events can be rejected)"

        if event.college_id != authority_college_id:
            return False, "You do not have authority over this event's college"

        if not reason or not reason.strip():
            return False, "A rejection reason is required"

        try:
            event.status = EventStatus.CANCELLED
            event.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(
                f"Event rejected: event_id={event_id} by college_id={authority_college_id} "
                f"reason='{reason}'"
            )
            # TODO: Notify event creator with reason (notification system not yet implemented)
            return True, "Event rejected and cancelled"
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to reject event_id={event_id} for college_id={authority_college_id}: {e}"
            )
            return False, "Failed to reject event"

    @staticmethod
    def cancel_event(event_id, user_id=None, authority_college_id=None):
        """
        Cancel an event. Blocked on COMPLETED events (terminal state).

        Caller identity rules:
        - Regular user (user_id provided): can cancel only their own event,
          only from DRAFT or ACTIVE.
        - College authority (authority_college_id provided): can cancel any
          non-terminal event belonging to their college.

        Exactly one of user_id or authority_college_id must be provided.

        Args:
            event_id (int)
            user_id (int, optional): regular user's id
            authority_college_id (int, optional): college authority's college_id

        Returns:
            (bool, str)
        """
        if (user_id is None) == (authority_college_id is None):
            # Both provided or neither provided — programming error
            return False, "Exactly one of user_id or authority_college_id must be provided"

        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found"

        if not EventService.can_transition(event.status, EventStatus.CANCELLED):
            return False, f"Cannot transition from {event.status} to cancelled"

        if user_id is not None:
            # Regular user: must be creator
            if event.created_by != user_id:
                return False, "You do not have permission to cancel this event"
        else:
            # College authority: must match event's college
            if event.college_id != authority_college_id:
                return False, "You do not have authority over this event's college"

        try:
            event.status = EventStatus.CANCELLED
            event.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            actor = f"user_id={user_id}" if user_id else f"college_id={authority_college_id}"
            logger.info(f"Event cancelled: event_id={event_id} by {actor}")
            return True, "Event cancelled successfully"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cancel event_id={event_id}: {e}")
            return False, "Failed to cancel event"

    @staticmethod
    def complete_event(event_id, user_id=None, authority_college_id=None):
        """
        Mark an event as completed. Transitions ACTIVE → COMPLETED.
        Awards event_organized XP to the event creator. XP failure is non-fatal.

        Caller identity rules:
        - Regular user (user_id provided): must be the event creator.
        - College authority (authority_college_id provided): must match event.college_id.

        Exactly one of user_id or authority_college_id must be provided.

        Args:
            event_id (int)
            user_id (int, optional)
            authority_college_id (int, optional)

        Returns:
            (bool, str)
        """
        if (user_id is None) == (authority_college_id is None):
            return False, "Exactly one of user_id or authority_college_id must be provided"

        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found"

        if not EventService.can_transition(event.status, EventStatus.COMPLETED):
            return False, f"Cannot transition from {event.status} to completed (only active events can be completed)"

        if user_id is not None:
            if event.created_by != user_id:
                return False, "Only the event creator can mark this event as completed"
        else:
            if event.college_id != authority_college_id:
                return False, "You do not have authority over this event's college"

        try:
            event.status = EventStatus.COMPLETED
            event.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            actor = f"user_id={user_id}" if user_id else f"college_id={authority_college_id}"
            logger.info(f"Event completed: event_id={event_id} by {actor}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to complete event_id={event_id}: {e}")
            return False, "Failed to complete event"

        # Award event_organized XP to the creator — non-fatal
        try:
            creator = db.session.get(User, event.created_by)
            if creator:
                XPService.award_standard_xp(
                    creator,
                    "event_organized",
                    description=f"Organized event: {event.event_name}",
                    related_entity_type="Event",
                    related_entity_id=event.event_id,
                )
        except Exception as e:
            logger.warning(
                f"Non-fatal: event_organized XP award failed for "
                f"creator_id={event.created_by} on event_id={event_id}: {e}"
            )

        return True, "Event marked as completed"

    # ===========================================================================
    # GROUP 2 — PARTICIPATION
    # ===========================================================================

    @staticmethod
    def check_user_eligibility(event, user):
        """
        Check whether a user meets all requirements to participate in an event.

        This method was migrated from Event.can_user_participate() which was an
        architectural violation (business logic + inline DB queries on a model).

        Checks (in order):
        1. Event is active
        2. Event is verified
        3. College restriction
        4. Capacity (dynamic count — no current_participants column)
        5. Requirement: min_level
        6. Requirement: min_xp
        7. Requirement: min_language_proficiency

        Args:
            event (Event): Event instance
            user (User): User instance

        Returns:
            (bool, str)
        """
        if event.status != EventStatus.ACTIVE:
            return False, f"Event is not open for registration (status: {event.status})"

        if not event.is_verified:
            return False, "Event has not been verified"

        if event.is_college_specific and user.college_id != event.college_id:
            return False, "This event is only open to students from the hosting college"

        # Capacity check (TOCTOU known limitation — acceptable for v1)
        if event.max_participants is not None:
            current_count = EventParticipant.query.filter_by(
                event_id=event.event_id
            ).filter(
                EventParticipant.registration_status.in_([
                    ParticipantStatus.REGISTERED,
                    ParticipantStatus.CONFIRMED,
                    ParticipantStatus.COMPLETED,
                ])
            ).count()
            if current_count >= event.max_participants:
                return False, "This event is full"

        if event.requirements:
            min_level = event.requirements.get("min_level")
            if min_level and user.level < min_level:
                return False, f"Requires level {min_level} (you are level {user.level})"

            min_xp = event.requirements.get("min_xp")
            if min_xp and user.xp < min_xp:
                return False, f"Requires {min_xp} XP (you have {user.xp} XP)"

            lang_requirements = event.requirements.get("min_language_proficiency", {})
            for lang_name, min_proficiency in lang_requirements.items():
                lang_obj = Language.query.filter_by(name=lang_name).first()
                user_lang = (
                    UserLanguage.query.filter_by(
                        user_id=user.id,
                        language_id=lang_obj.id,
                    ).first()
                    if lang_obj
                    else None
                )
                if not user_lang or user_lang.language_level < min_proficiency:
                    return (
                        False,
                        f"Requires {lang_name} proficiency level {min_proficiency}",
                    )

        return True, "Eligible to participate"

    @staticmethod
    def register_for_event(event_id, user_id):
        """
        Register a user for an event.

        Checks:
        - Event exists
        - User exists
        - Not already registered (or previously dropped — re-registration allowed
          only if prior record is in DROPPED status)
        - Eligibility via check_user_eligibility()

        Awards event_rsvp (5 XP) on success. Non-fatal.

        Args:
            event_id (int)
            user_id (int)

        Returns:
            (bool, str, EventParticipant|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found", None

        # Check for existing participation record
        existing = EventParticipant.query.filter_by(
            event_id=event_id,
            user_id=user_id,
        ).first()

        if existing:
            if existing.registration_status != ParticipantStatus.DROPPED:
                return False, "You are already registered for this event", None
            # Re-registration after drop: re-check eligibility before resetting the record
            eligible, reason = EventService.check_user_eligibility(event, user)
            if not eligible:
                return False, reason, None
            existing.registration_status = ParticipantStatus.REGISTERED
            existing.registered_at = datetime.now(timezone.utc)
            existing.completed_at = None
            participant = existing
        else:
            eligible, reason = EventService.check_user_eligibility(event, user)
            if not eligible:
                return False, reason, None

            participant = EventParticipant(
                event_id=event_id,
                user_id=user_id,
                registration_status=ParticipantStatus.REGISTERED,
            )
            db.session.add(participant)

        try:
            db.session.commit()
            logger.info(f"User registered: user_id={user_id} event_id={event_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to register user_id={user_id} for event_id={event_id}: {e}")
            return False, "Failed to register for event", None

        # Award event_rsvp XP — non-fatal
        try:
            XPService.award_standard_xp(
                user,
                "event_rsvp",
                description=f"RSVP'd to event: {event.event_name}",
                related_entity_type="Event",
                related_entity_id=event_id,
            )
        except Exception as e:
            logger.warning(
                f"Non-fatal: event_rsvp XP award failed for user_id={user_id} "
                f"event_id={event_id}: {e}"
            )

        return True, "Successfully registered for event", participant

    @staticmethod
    def confirm_attendance(event_id, user_id):
        """
        Self-confirm attendance within the check-in time window.

        Window: event.start_time <= now <= event.start_time + CHECK_IN_WINDOW_HOURS

        Transitions participant status: REGISTERED → CONFIRMED.

        Awards on success (both non-fatal):
        - event_attended (50 XP) from XP_AMOUNTS constant
        - event.completion_xp bonus (if > 0), also sourced as 'event_attended'
          so it counts against the same daily cap bucket

        Args:
            event_id (int)
            user_id (int)

        Returns:
            (bool, str, EventParticipant|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        participant = EventParticipant.query.filter_by(
            event_id=event_id,
            user_id=user_id,
        ).first()

        if not participant:
            return False, "You are not registered for this event", None

        if participant.registration_status != ParticipantStatus.REGISTERED:
            return (
                False,
                f"Cannot confirm attendance from status: {participant.registration_status}",
                None,
            )

        # Time-window check
        now = datetime.now(timezone.utc)
        # Normalise event.start_time to UTC-aware for comparison
        start = event.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        window_end = start + timedelta(hours=CHECK_IN_WINDOW_HOURS)

        if now < start:
            return False, "Check-in window has not opened yet (event has not started)", None
        if now > window_end:
            return (
                False,
                f"Check-in window has closed (opens at event start, closes {CHECK_IN_WINDOW_HOURS}h later)",
                None,
            )

        try:
            participant.registration_status = ParticipantStatus.CONFIRMED
            participant.completed_at = now
            db.session.commit()
            logger.info(f"Attendance confirmed: user_id={user_id} event_id={event_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to confirm attendance for user_id={user_id} event_id={event_id}: {e}"
            )
            return False, "Failed to confirm attendance", None

        # Award XP — non-fatal block
        user = db.session.get(User, user_id)
        if user:
            try:
                XPService.award_standard_xp(
                    user,
                    "event_attended",
                    description=f"Attended event: {event.event_name}",
                    related_entity_type="Event",
                    related_entity_id=event_id,
                )
            except Exception as e:
                logger.warning(
                    f"Non-fatal: event_attended XP failed for user_id={user_id} "
                    f"event_id={event_id}: {e}"
                )

            if event.completion_xp and event.completion_xp > 0:
                try:
                    XPService.award_xp(
                        user,
                        event.completion_xp,
                        source="event_attended",
                        description=f"Completion bonus for event: {event.event_name}",
                        related_entity_type="Event",
                        related_entity_id=event_id,
                    )
                except Exception as e:
                    logger.warning(
                        f"Non-fatal: completion_xp award failed for user_id={user_id} "
                        f"event_id={event_id}: {e}"
                    )

        return True, "Attendance confirmed", participant

    @staticmethod
    def drop_from_event(event_id, user_id):
        """
        Drop a user from an event. No XP clawback.

        Valid from REGISTERED or CONFIRMED status only.
        Terminal statuses (COMPLETED, DROPPED) cannot transition.

        Args:
            event_id (int)
            user_id (int)

        Returns:
            (bool, str)
        """
        participant = EventParticipant.query.filter_by(
            event_id=event_id,
            user_id=user_id,
        ).first()

        if not participant:
            return False, "You are not registered for this event"

        current = participant.registration_status
        if ParticipantStatus.DROPPED not in VALID_PARTICIPANT_TRANSITIONS.get(current, []):
            return False, f"Cannot drop from current status: {current}"

        try:
            participant.registration_status = ParticipantStatus.DROPPED
            db.session.commit()
            logger.info(f"User dropped: user_id={user_id} event_id={event_id}")
            return True, "Successfully dropped from event"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to drop user_id={user_id} from event_id={event_id}: {e}")
            return False, "Failed to drop from event"

    @staticmethod
    def get_event_participants(event_id, status_filter=None):
        """
        Return participants for an event, optionally filtered by status.

        This replaces the removed current_participants column.
        Count is always computed dynamically from this query result.

        Args:
            event_id (int)
            status_filter (str|None): ParticipantStatus constant, or None for all

        Returns:
            list[EventParticipant]
        """
        query = EventParticipant.query.filter_by(event_id=event_id)
        if status_filter:
            query = query.filter_by(registration_status=status_filter)
        return query.all()

    # ===========================================================================
    # GROUP 3 — EVENT TASKS
    # ===========================================================================

    @staticmethod
    def create_event_task(event_id, creator_id, data):
        """
        Create a task for an event.

        Only the event creator can add tasks.
        Event must not be in a terminal state (COMPLETED or CANCELLED).

        Validates the actions array schema:
            [{"id": int, "text": str, "xp": int}, ...]

        Args:
            event_id (int)
            creator_id (int): must match event.created_by
            data (dict): {
                title (str),
                description (str, optional),
                difficulty (str): "Easy"|"Medium"|"Hard",
                xp_reward (int),
                actions (list),
                is_required (bool),
            }

        Returns:
            (bool, str, EventTask|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        if event.created_by != creator_id:
            return False, "Only the event creator can add tasks", None

        if event.status in (EventStatus.COMPLETED, EventStatus.CANCELLED):
            return False, f"Cannot add tasks to a {event.status} event", None

        if not data.get("title", "").strip():
            return False, "Task title is required", None

        difficulty = data.get("difficulty", "Medium")
        if difficulty not in VALID_TASK_DIFFICULTIES:
            return False, f"Invalid difficulty. Must be one of: {', '.join(VALID_TASK_DIFFICULTIES)}", None

        actions = data.get("actions")
        valid, error = EventService._validate_actions(actions)
        if not valid:
            return False, error, None

        try:
            task = EventTask(
                event_id=event_id,
                title=data["title"].strip(),
                description=data.get("description", "").strip() or None,
                difficulty=difficulty,
                xp_reward=int(data.get("xp_reward", 0)),
                actions=actions,
                is_required=bool(data.get("is_required", False)),
            )
            db.session.add(task)
            db.session.commit()
            logger.info(
                f"EventTask created: task_id={task.task_id} event_id={event_id} "
                f"by creator_id={creator_id}"
            )
            return True, "Task created successfully", task
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create task for event_id={event_id}: {e}")
            return False, "Failed to create task", None

    @staticmethod
    def get_event_tasks(event_id):
        """
        Return all tasks for an event. No auth check — visible to all participants.

        Args:
            event_id (int)

        Returns:
            list[EventTask]
        """
        return EventTask.query.filter_by(event_id=event_id).all()

    @staticmethod
    def submit_task_action(event_task_id, user_id, action_id):
        """
        Submit a task action completion for a user.

        Flow:
        1. Validate task and event exist and are active
        2. Confirm user is a confirmed participant
        3. Validate action_id exists in task.actions
        4. Check not already submitted
        5. Create EventTaskCompletion with status=pending_verification
        6. Pass to verification stub (auto-approves for v1)

        Args:
            event_task_id (int)
            user_id (int)
            action_id (int)

        Returns:
            (bool, str, EventTaskCompletion|None)
        """
        task = db.session.get(EventTask, event_task_id)
        if not task:
            return False, "Task not found", None

        event = db.session.get(Event, task.event_id)
        if not event or event.status != EventStatus.ACTIVE:
            return False, "Event is not active", None

        # User must be a confirmed participant
        participant = EventParticipant.query.filter_by(
            event_id=task.event_id,
            user_id=user_id,
            registration_status=ParticipantStatus.CONFIRMED,
        ).first()

        if not participant:
            return False, "You must confirm attendance before submitting task actions", None

        # Validate action exists in the task
        action = EventService._get_action_by_id(task.actions, action_id)
        if not action:
            return False, f"Action {action_id} not found in this task", None

        # Prevent duplicate submission
        existing = EventTaskCompletion.query.filter_by(
            event_task_id=event_task_id,
            user_id=user_id,
            action_id=action_id,
        ).first()
        if existing:
            return False, "You have already submitted this action", None

        try:
            completion = EventTaskCompletion(
                event_task_id=event_task_id,
                user_id=user_id,
                action_id=action_id,
                status=TaskCompletionStatus.PENDING_VERIFICATION,
                submitted_at=datetime.now(timezone.utc),
            )
            db.session.add(completion)
            db.session.flush()  # Needed so completion.id exists before stub call

            # TODO: Plug verification engine here.
            # The engine should inspect submission type, validate evidence,
            # and call _approve_action_completion(completion, action) or
            # _reject_action_completion(completion, reason).
            # For now, auto-approve as stub:
            EventService._auto_approve_stub(completion, action)

            db.session.commit()
            logger.info(
                f"Task action submitted and auto-approved: "
                f"user_id={user_id} task_id={event_task_id} action_id={action_id}"
            )
            return True, "Action submitted and approved", completion
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to submit action_id={action_id} for task_id={event_task_id} "
                f"user_id={user_id}: {e}"
            )
            return False, "Failed to submit task action", None

    @staticmethod
    def get_task_completion_summary(event_task_id, user_id):
        """
        Return a summary of a user's progress on a specific task.

        Args:
            event_task_id (int)
            user_id (int)

        Returns:
            dict: {
                task_id, total_actions, completed_actions,
                completion_percentage, total_xp_earned, actions_detail
            }
            Returns None if task not found.
        """
        task = db.session.get(EventTask, event_task_id)
        if not task:
            return None

        completions = EventTaskCompletion.query.filter_by(
            event_task_id=event_task_id,
            user_id=user_id,
            status=TaskCompletionStatus.APPROVED,
        ).all()

        approved_action_ids = {c.action_id for c in completions}
        total_xp = sum(c.xp_awarded for c in completions)
        total_actions = len(task.actions) if task.actions else 0
        completed_count = len(approved_action_ids)

        completion_pct = (
            round((completed_count / total_actions) * 100, 1)
            if total_actions > 0
            else 0.0
        )

        actions_detail = []
        for action in (task.actions or []):
            actions_detail.append({
                "action_id": action["id"],
                "text": action["text"],
                "xp": action["xp"],
                "completed": action["id"] in approved_action_ids,
            })

        return {
            "task_id": event_task_id,
            "total_actions": total_actions,
            "completed_actions": completed_count,
            "completion_percentage": completion_pct,
            "total_xp_earned": total_xp,
            "actions_detail": actions_detail,
        }

    # ===========================================================================
    # GROUP 4 — DISCOVERY AND QUERIES
    # ===========================================================================

    @staticmethod
    def get_event(event_id, user_id):
        """
        Fetch a single event, enforcing college restriction.

        A college-specific event is only visible to users from that college.

        Args:
            event_id (int)
            user_id (int)

        Returns:
            (bool, str, Event|None)
        """
        event = db.session.get(Event, event_id)
        if not event:
            return False, "Event not found", None

        if event.is_college_specific:
            user = db.session.get(User, user_id)
            if not user or user.college_id != event.college_id:
                return False, "You do not have access to this event", None

        return True, "Event retrieved", event

    @staticmethod
    def list_events(user_id, filters=None):
        """
        List active events visible to the user, ordered by start_time ascending.

        Filters applied:
        - status = ACTIVE always enforced
        - College-specific events filtered to user's college only
        - Optional filters dict: {event_type, college_id}

        Args:
            user_id (int)
            filters (dict|None)

        Returns:
            list[Event]
        """
        user = db.session.get(User, user_id)

        query = Event.query.filter_by(status=EventStatus.ACTIVE)

        # Restrict college-specific events to the user's own college
        if user and user.college_id:
            query = query.filter(
                db.or_(
                    Event.is_college_specific == False,
                    Event.college_id == user.college_id,
                )
            )
        else:
            query = query.filter(Event.is_college_specific == False)

        if filters:
            if filters.get("event_type"):
                query = query.filter_by(event_type=filters["event_type"])

        query = query.order_by(Event.start_time.asc())
        return query.all()

    # ===========================================================================
    # GROUP 5 — AUTHORITY QUERIES
    # ===========================================================================

    @staticmethod
    def get_pending_events(authority_college_id):
        """
        Return all pending events for a college.

        Only pending events (awaiting approval) are returned.
        The route is responsible for verifying the caller is a valid
        college authority before calling this method.

        Args:
            authority_college_id (int): college_id from the authority's JWT

        Returns:
            list[Event]
        """
        return (
            Event.query
            .filter_by(
                college_id=authority_college_id,
                status=EventStatus.PENDING,
            )
            .order_by(Event.created_at.asc())
            .all()
        )

    # ===========================================================================
    # PRIVATE HELPERS
    # ===========================================================================

    @staticmethod
    def _validate_actions(actions):
        """
        Validate the actions JSON array structure.

        Expected: [{"id": int, "text": str, "xp": int}, ...]
        - Must be a non-empty list
        - Each item must have id (int), text (non-empty str), xp (int >= 0)
        - ids must be unique within the list

        Returns:
            (bool, str|None): (is_valid, error_message)
        """
        if not actions or not isinstance(actions, list):
            return False, "Actions must be a non-empty list"

        seen_ids = set()
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                return False, f"Action at index {i} must be an object"

            if not isinstance(action.get("id"), int):
                return False, f"Action at index {i} must have an integer 'id'"

            if action["id"] in seen_ids:
                return False, f"Duplicate action id: {action['id']}"
            seen_ids.add(action["id"])

            if not isinstance(action.get("text"), str) or not action["text"].strip():
                return False, f"Action {action['id']} must have a non-empty 'text' string"

            if not isinstance(action.get("xp"), int) or action["xp"] < 0:
                return False, f"Action {action['id']} must have a non-negative integer 'xp'"

        return True, None

    @staticmethod
    def _get_action_by_id(actions, action_id):
        """
        Find a specific action in a task's actions list by id.

        Args:
            actions (list): task.actions JSON array
            action_id (int)

        Returns:
            dict|None
        """
        if not actions:
            return None
        for action in actions:
            if action.get("id") == action_id:
                return action
        return None

    @staticmethod
    def _auto_approve_stub(completion, action):
        """
        Auto-approve a task action completion for v1.

        This is a deliberately minimal stub. The verification engine
        will replace this call in submit_task_action() — one call site,
        clearly marked with a TODO above.

        Sets completion.status = APPROVED and awards action XP to the user.
        XP failure is non-fatal and logged as a warning.

        Args:
            completion (EventTaskCompletion): flushed but not yet committed
            action (dict): the action dict from task.actions
        """
        action_xp = action.get("xp", 0)

        completion.status = TaskCompletionStatus.APPROVED
        completion.reviewed_at = datetime.now(timezone.utc)
        completion.xp_awarded = action_xp
        # reviewed_by remains None — auto-approved, no human reviewer

        # Award XP — non-fatal
        try:
            user = db.session.get(User, completion.user_id)
            if user and action_xp > 0:
                XPService.award_xp(
                    user,
                    action_xp,
                    source="task_complete",
                    description=f"Completed task action {completion.action_id}",
                    related_entity_type="EventTask",
                    related_entity_id=completion.event_task_id,
                )
        except Exception as e:
            logger.warning(
                f"Non-fatal: XP award failed in _auto_approve_stub for "
                f"user_id={completion.user_id} action_id={completion.action_id}: {e}"
            )


# Singleton instance — import this in routes
event_service = EventService()
