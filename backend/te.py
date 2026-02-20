from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    result = db.session.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_languages'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(row)