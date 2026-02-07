from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# 🔐 where unauthenticated users are redirected
login_manager.login_view = "auth_routes.user_login"
