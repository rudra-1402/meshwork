import os

class Config:
    # Core Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:Rudra#9936@localhost:5432/meshwork')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    