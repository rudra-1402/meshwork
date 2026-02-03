from app.extensions import db

class College(db.Model):
    __tablename__ = "colleges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # ✅ relationship (depends on FK in User)
    users = db.relationship("User", back_populates="college")

    def __repr__(self):
        return f"<College {self.name}>"
