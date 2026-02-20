"""
Event Module Constants

All event-related enums, state machines, permission thresholds,
and timing constants in one centralized location.

Do NOT use raw strings for status values anywhere in the event service or routes.
Always import and use these constants.
"""


# ===== STATUS ENUMS =====

class EventStatus:
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventCreatorType:
    COLLEGE = "college"
    COMMUNITY = "community"
    USER = "user"


class ParticipantStatus:
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    DROPPED = "dropped"


class TaskCompletionStatus:
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    REJECTED = "rejected"


# ===== STATE MACHINES =====
# These are the ONLY valid transitions. The service enforces these strictly.
# Terminal states (COMPLETED, CANCELLED) have empty lists — no exits.

VALID_EVENT_TRANSITIONS = {
    EventStatus.DRAFT:      [EventStatus.PENDING, EventStatus.ACTIVE, EventStatus.CANCELLED],
    EventStatus.PENDING:    [EventStatus.ACTIVE, EventStatus.CANCELLED],
    EventStatus.ACTIVE:     [EventStatus.COMPLETED, EventStatus.CANCELLED],
    EventStatus.COMPLETED:  [],
    EventStatus.CANCELLED:  [],
}

VALID_PARTICIPANT_TRANSITIONS = {
    ParticipantStatus.REGISTERED:  [ParticipantStatus.CONFIRMED, ParticipantStatus.DROPPED],
    ParticipantStatus.CONFIRMED:   [ParticipantStatus.COMPLETED, ParticipantStatus.DROPPED],
    ParticipantStatus.COMPLETED:   [],
    ParticipantStatus.DROPPED:     [],
}


# ===== PERMISSION THRESHOLDS =====

# Minimum user level required to create an event.
# Applies to regular users and community leaders.
# College authority is exempt from this gate.
MIN_LEVEL_TO_CREATE_EVENT = 100


# ===== ATTENDANCE TIMING =====

# Self check-in window: participant can confirm attendance
# only within this many hours after event start_time.
#
# Known limitation: self-reported within a time window — gameable
# if check-in timing is leaked. QR-based check-in was evaluated
# and deferred (no other module uses QR). Acceptable for v1.
CHECK_IN_WINDOW_HOURS = 24


# ===== TASK VALIDATION =====

# Valid difficulty values for EventTask.
VALID_TASK_DIFFICULTIES = {"Easy", "Medium", "Hard"}
