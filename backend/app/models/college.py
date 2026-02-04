from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class College(db.Model):
    __tablename__ = "colleges"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # 🔗 One college → many users
    users = db.relationship(
        "User",
        back_populates="college",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
