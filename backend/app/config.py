import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:dhruv_2607@localhost:5432/meshwork"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
