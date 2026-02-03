from app.extensions import db

class Interest(db.Model):
    __tablename__ = "interests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Interest {self.name}>"
