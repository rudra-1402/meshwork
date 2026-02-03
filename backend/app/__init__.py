from flask import Flask
from app.config import Config
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)

    # Basic configuration
    app.config.from_object('app.config.Config')

    # Import models to register them with SQLAlchemy and so alembic can detect changes
    from app.models.user import User

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register routes
    from app.routes.main_routes import main_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.dashboard_routes import dashboard_routes

    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(dashboard_routes)

    # Register error handlers
    from app.error_handlers import register_error_handlers
    
    register_error_handlers(app)

    return app
