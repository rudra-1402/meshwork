from flask import Flask
from app.config import Config
from datetime import timedelta
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_NAME'] = 'access_token_cookie'
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Enable CSRF in production
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_DECODE_LEEWAY'] = 10  # Allow 10 seconds of leeway for clock skew
    # Extended to 24 hours for better user experience (reduce in production if needed)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Set timeout for long-running operations like Ollama AI scoring
    # Allows up to 2 minutes for AI model inference
    app.config['TIMEOUT'] = 120
    # ✅ INIT EXTENSIONS FIRST
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)
    
    # ✅ JWT ERROR HANDLERS
    from flask import flash, redirect, url_for, request
    import logging
    
    logger = logging.getLogger(__name__)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.warning(f"Missing JWT token for {request.path}")
        flash("Please log in to access this page.", "error")
        return redirect(url_for("auth.user_login")), 302
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning(f"Invalid JWT token for {request.path}: {error}")
        flash("Your session has expired. Please log in again.", "error")
        return redirect(url_for("auth.user_login")), 302
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        logger.warning(f"Expired JWT token for {request.path}")
        flash("Your session has expired. Please log in again.", "error")
        return redirect(url_for("auth.user_login")), 302

    # ✅ IMPORT *ALL* MODELS (VERY IMPORTANT)
    from app.models.user import User
    from app.models.college import College
    from app.models.scoring import UserScoring
    from app.models.scoring_history import ScoringHistory
    from app.models.user_language import UserLanguage

    # ✅ REGISTER BLUEPRINTS
    from app.routes.main_routes import main_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.college_auth_routes import college_auth_routes
    from app.routes.dashboard_routes import dashboard_routes
    from app.routes.scoring_routes import scoring_bp

    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(college_auth_routes)
    app.register_blueprint(dashboard_routes, url_prefix="")
    app.register_blueprint(scoring_bp, url_prefix="/scoring")

    return app
