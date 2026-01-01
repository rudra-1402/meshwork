from flask import Flask

def create_app():
    app = Flask(__name__)

    # Basic configuration
    app.config.from_object('app.config.Config')

    # Register routes
    from app.routes.main_routes import main_routes
    from app.routes.auth_routes import auth_routes
    from app.routes.dashboard_routes import dashboard_routes

    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(dashboard_routes)

    return app
