import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:astha@localhost:5432/meshwork')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    