from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
import logging

logger = logging.getLogger(__name__)

# Role-based enforcement not yet implemented; use specific decorators per route.
def login_required(fn):
    """
    JWT-based login_required decorator.

    Usage:
        @login_required
        def my_view():
            ...

    Verifies a valid JWT is present. Does not enforce user roles —
    use route-specific decorators (e.g. personnel_required, admin_required)
    for role checks.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Verify JWT token exists and is valid
            verify_jwt_in_request()
            identity = get_jwt_identity()

            if identity is None:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource.'
                }), 401

            return fn(*args, **kwargs)

        except NoAuthorizationError as e:
            # No JWT token found
            logger.debug(f"No authorization for {request.path}: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource.'
            }), 401

        except Exception as e:
            # Token invalid/expired or other JWT error
            logger.error(f"JWT error for {request.path}: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Your session has expired. Please log in again.'
            }), 401

    return wrapper
