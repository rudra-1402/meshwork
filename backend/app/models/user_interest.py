from app.extensions import db

user_interests = db.Table(
    "user_interests",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("interest_id", db.Integer, db.ForeignKey("interests.id"), primary_key=True),
)
