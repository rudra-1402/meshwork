from app import create_app
from app.extensions import db
from sqlalchemy import inspect

def check_tables():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Existing tables:", tables)

if __name__ == "__main__":
    check_tables()