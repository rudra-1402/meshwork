from app import create_app
from app.extensions import db
from sqlalchemy import text

def update_alembic_version():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            connection.execute(text("DELETE FROM alembic_version"))
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('head')"))
            print("Alembic version updated to 'head'")

if __name__ == "__main__":
    update_alembic_version()