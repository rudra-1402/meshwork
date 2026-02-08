import logging

from flask import flash, redirect, url_for
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger(__name__)


def get_user_id_or_redirect():
    identity = get_jwt_identity()
    if not identity:
        flash("Please log in to access this page.", "error")
        return None, redirect(url_for("auth.user_login"))

    identity_str = str(identity)
    if identity_str.startswith("college_"):
        flash("Access denied. User login required.", "error")
        return None, redirect(url_for("auth.user_login"))

    try:
        return int(identity_str), None
    except (TypeError, ValueError):
        logger.warning("Invalid user identity: %s", identity)
        flash("Your session is invalid. Please log in again.", "error")
        return None, redirect(url_for("auth.user_login"))


def get_college_id_or_redirect():
    identity = get_jwt_identity()
    if not identity:
        flash("Please log in to access this page.", "error")
        return None, redirect(url_for("college_auth.college_login"))

    identity_str = str(identity)
    if not identity_str.startswith("college_"):
        flash("Access denied. College login required.", "error")
        return None, redirect(url_for("college_auth.college_login"))

    raw_id = identity_str.replace("college_", "", 1)
    try:
        return int(raw_id), None
    except (TypeError, ValueError):
        logger.warning("Invalid college identity: %s", identity)
        flash("Your session is invalid. Please log in again.", "error")
        return None, redirect(url_for("college_auth.college_login"))
