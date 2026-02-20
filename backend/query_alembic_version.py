from app import create_app
from app.extensions import db
from sqlalchemy import text

def query_alembic_version():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(text('SELECT * FROM alembic_version')).fetchall()
            print(result)

if __name__ == "__main__":
    query_alembic_version()