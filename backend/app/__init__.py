from flask import Flask, jsonify, request
from flask_cors import CORS
from app.config import Config
from datetime import timedelta
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ✅ CORS CONFIGURATION (React SPA)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # ✅ JWT CONFIGURATION (Header-based for SPA)
    app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_TOKEN_LOCATION'] = ['headers']  # Changed from cookies to headers
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_DECODE_LEEWAY'] = 10
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['TIMEOUT'] = 120
    
    # ✅ INIT EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)
    
    # ✅ JWT ERROR HANDLERS (API-friendly JSON responses)
    import logging
    logger = logging.getLogger(__name__)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logger.warning(f"Missing JWT token for {request.path}")
        return jsonify({
            'success': False,
            'message': 'Authorization token is missing'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logger.warning(f"Invalid JWT token for {request.path}: {error}")
        return jsonify({
            'success': False,
            'message': 'Invalid authorization token'
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        logger.warning(f"Expired JWT token for {request.path}")
        return jsonify({
            'success': False,
            'message': 'Authorization token has expired'
        }), 401
    
    # ================= IMPORT MODELS =================
    # (Required so Flask-Migrate can detect tables)
    
    # Core models
    from app.models.user import User
    from app.models.college import College
    from app.models.college_personnel import CollegePersonnel
    from app.models.whitelisted_email import WhitelistedEmail
    
    # Scoring models
    from app.models.scoring import UserScoring
    from app.models.scoring_history import ScoringHistory
    from app.models.user_language import UserLanguage
    
    # Community models
    from app.models.community import Community
    from app.models.community_member import CommunityMember
    from app.models.community_moderator import CommunityModerator
    from app.models.community_task import CommunityTask
    from app.models.task_completion import TaskCompletion
    from app.models.community_message import CommunityMessage
    from app.models.community_poll import CommunityPoll, PollVote
    from app.models.community_file import CommunityFile
    
    # Event models
    from app.models.event_models import Event, EventParticipant, EventTask
    
    # ✅ GAMIFICATION MODELS (NEW)
    from app.models.user_skill import UserSkill
    from app.models.xp_transaction import XPTransaction
    # Note: User model already imported above, but it now has gamification fields
    
    # ================= REGISTER BLUEPRINTS =================
    from app.routes.main_routes import main_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.college_auth_routes import college_auth_routes
    from app.routes.unified_auth_routes import unified_auth_routes
    from app.routes.dashboard_routes import dashboard_routes
    from app.routes.scoring_routes import scoring_bp
    from app.routes.community_routes import community_routes
    from app.routes.personnel_dashboard_routes import personnel_dashboard_routes
    from app.routes.profile_routes import profile_bp
    from app.routes.leaderboard_routes import leaderboards_bp
    from app.routes.admin_routes import admin_bp
    
    # Register all routes under /api prefix for clean API architecture
    app.register_blueprint(main_routes, url_prefix="/api")
    app.register_blueprint(auth_routes, url_prefix="/api/auth")
    app.register_blueprint(college_auth_routes, url_prefix="/api/college-auth")
    app.register_blueprint(unified_auth_routes)  # Has its own prefix /api/auth
    app.register_blueprint(dashboard_routes, url_prefix="/api/dashboard")
    app.register_blueprint(scoring_bp, url_prefix="/api/scoring")
    app.register_blueprint(community_routes, url_prefix="/api/communities")
    app.register_blueprint(personnel_dashboard_routes, url_prefix="/api/personnel")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(leaderboards_bp, url_prefix="/api/leaderboard")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    
    # ✅ Root route - API info
    @app.route('/')
    def root():
        return jsonify({
            'name': 'MeshWork API',
            'version': '2.0.0',
            'status': 'running',
            'message': 'This is an API server. Use /api/* endpoints.',
            'endpoints': {
                'health': '/api/health',
                'unified_auth': {
                    'validate_email': 'POST /api/auth/validate-email',
                    'login': 'POST /api/auth/login',
                    'signup': 'POST /api/auth/signup',
                    'check_username': 'POST /api/auth/check-username'
                },
                'docs': 'See UNIFIED_AUTH_TEST_COMMANDS.md for test examples'
            }
        }), 200
    
    # ✅ API Health Check
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'MeshWork API is running',
            'version': '2.0.0'
        }), 200
    
    return app