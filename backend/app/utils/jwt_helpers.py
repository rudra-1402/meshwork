import logging

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger(__name__)


def get_user_id_or_error():
    """
    Used by all event routes that require a student caller.
    Returns (user_id, None) on success.
    Returns (None, (jsonify_response, status_code)) on failure.
    """
    identity = get_jwt_identity()
    if identity is None:
        return None, (jsonify({"success": False, "message": "Authentication required."}), 401)

    identity_str = str(identity)
    if identity_str.startswith("personnel_"):
        return None, (jsonify({"success": False, "message": "Student authentication required."}), 403)

    try:
        return int(identity_str), None
    except (TypeError, ValueError):
        logger.warning("Invalid user identity in get_user_id_or_error: %s", identity)
        return None, (jsonify({"success": False, "message": "Invalid session. Please log in again."}), 401)


def get_personnel_id_or_error():
    """
    Used by all event routes that require a personnel (college authority) caller.
    Named 'personnel' to match actual JWT identity prefix 'personnel_XXXX'.
    Returns (personnel_id, None) on success.
    Returns (None, (jsonify_response, status_code)) on failure.
    """
    identity = get_jwt_identity()
    if identity is None:
        return None, (jsonify({"success": False, "message": "Authentication required."}), 401)

    identity_str = str(identity)
    if not identity_str.startswith("personnel_"):
        return None, (jsonify({"success": False, "message": "Personnel authentication required."}), 403)

    raw_id = identity_str.replace("personnel_", "", 1)
    try:
        return int(raw_id), None
    except (TypeError, ValueError):
        logger.warning("Invalid personnel identity in get_personnel_id_or_error: %s", identity)
        return None, (jsonify({"success": False, "message": "Invalid session. Please log in again."}), 401)