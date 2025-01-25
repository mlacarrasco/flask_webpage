import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', False)
    PORT = int(os.environ.get('PORT', 5000))
    
    # Add other configuration variables here
    SOCKETIO_ASYNC_MODE = 'threading'
    CORS_ALLOWED_ORIGINS = "*"