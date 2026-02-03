from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.interest import Interest
from app.models.user_interest import user_interests

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # 🔥 THIS IS THE KEY LINE (WITHOUT THIS = ERROR)
    college_id = db.Column(
        db.Integer,
        db.ForeignKey("colleges.id"),
        nullable=True
    )

    # 🔥 AND THIS MUST MATCH College.users
    college = db.relationship("College", back_populates="users")

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    interests = db.relationship(
        Interest,
        secondary=user_interests,
        backref="users"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
