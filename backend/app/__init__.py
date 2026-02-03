from flask import Flask
from app.config import Config
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ INIT EXTENSIONS FIRST
    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ IMPORT *ALL* MODELS (VERY IMPORTANT)
    from app.models.user import User
    from app.models.college import College
    from app.models.interest import Interest
    from app.models.user_interest import user_interests

    # ✅ REGISTER BLUEPRINTS
    from app.routes.main_routes import main_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.college_auth_routes import college_auth_routes
    from app.routes.dashboard_routes import dashboard_routes
    from app.routes.onboarding_routes import onboarding_routes

    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(college_auth_routes)
    app.register_blueprint(dashboard_routes)
    app.register_blueprint(onboarding_routes)

    return app
