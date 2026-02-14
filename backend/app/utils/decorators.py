from functools import wraps
from flask import redirect, url_for, flash, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
import logging

logger = logging.getLogger(__name__)

def login_required(route_function=None, *, role=None):
    """
    JWT-based login_required decorator.
    
    Usage (existing code - still works):
        @login_required
    
    New usage (optional):
        @login_required(role="user")
        @login_required(role="college")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # ✅ Verify JWT token exists and is valid
                verify_jwt_in_request()
                identity = get_jwt_identity()
                
                if not identity:
                    flash("Please log in to access this page.", "error")
                    return redirect(url_for("auth.user_login"))
                
                # ✅ Role-specific checks (optional - requires storing role in JWT claims)
                if role == "user":
                    # If you store role in JWT claims, check it here
                    # from flask_jwt_extended import get_jwt
                    # claims = get_jwt()
                    # if claims.get("role") != "user":
                    #     flash("Access denied.", "error")
                    #     return redirect(url_for("auth.user_login"))
                    pass
                
                elif role == "college":
                    # If you store role in JWT claims, check it here
                    # from flask_jwt_extended import get_jwt
                    # claims = get_jwt()
                    # if claims.get("role") != "college":
                    #     flash("Access denied.", "error")
                    #     return redirect(url_for("college_auth.college_login"))
                    pass
                
                return fn(*args, **kwargs)
                
            except NoAuthorizationError as e:
                # No JWT token found
                logger.debug(f"No authorization for {request.path}: {str(e)}")
                flash("Please log in to access this page.", "error")
                if role == "college":
                    return redirect(url_for("college_auth.college_login"))
                return redirect(url_for("auth.user_login"))
            
            except Exception as e:
                # Token invalid/expired or other JWT error
                logger.error(f"JWT error for {request.path}: {str(e)}")
                flash("Your session has expired. Please log in again.", "error")
                if role == "college":
                    return redirect(url_for("college_auth.college_login"))
                return redirect(url_for("auth.user_login"))
        
        return wrapper

    # ✅ This makes @login_required (without parentheses) still work
    if route_function:
        return decorator(route_function)

    return decorator