"""
Configuration management for Arrears Manager API
Supports multiple environments: development, staging, production
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    
    # CORS
    CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', 'http://localhost,capacitor://localhost').split(',')]
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With', 'X-Idempotency-Key', 'X-Device-Id', 'X-App-Version', 'X-Platform']
    CORS_EXPOSE_HEADERS = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset', 'ETag', 'X-Correlation-Id']
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 86400  # 24 hours
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///arrears_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', 10))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 20))
    SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', 30))
    SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600))
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 3600,
    }
    
    # Caching
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_SWALLOW_ERRORS = False
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'csv,xlsx,xls').split(','))
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1048576))  # 1MB
    
    # Compression
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/plain'
    ]
    COMPRESS_LEVEL = int(os.getenv('COMPRESSION_LEVEL', 6))
    COMPRESS_MIN_SIZE = int(os.getenv('MIN_COMPRESSION_SIZE', 500))
    COMPRESS_ALGORITHM = ['gzip', 'br'] if os.getenv('ENABLE_BROTLI', 'True') == 'True' else ['gzip']
    
    # Timeouts (mobile-optimized)
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 15))
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', 30))
    KEEPALIVE_TIMEOUT = int(os.getenv('KEEPALIVE_TIMEOUT', 60))
    
    # Firebase Cloud Messaging
    FCM_CREDENTIALS_PATH = os.getenv('FCM_CREDENTIALS_PATH', './firebase-credentials.json')
    FCM_PROJECT_ID = os.getenv('FCM_PROJECT_ID', '')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # API Configuration
    API_VERSION = os.getenv('API_VERSION', 'v1')
    API_TITLE = os.getenv('API_TITLE', 'Arrears Manager API')
    API_DESCRIPTION = os.getenv('API_DESCRIPTION', 'Mobile-optimized API for loan analysis')
    
    # Security Headers
    ENABLE_HSTS = os.getenv('ENABLE_HSTS', 'True') == 'True'
    HSTS_MAX_AGE = int(os.getenv('HSTS_MAX_AGE', 31536000))
    ENABLE_CSP = os.getenv('ENABLE_CSP', 'True') == 'True'
    ENABLE_XSS_PROTECTION = os.getenv('ENABLE_XSS_PROTECTION', 'True') == 'True'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Response Size Limits
    MAX_RESPONSE_SIZE = 10485760  # 10MB


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Disable some security features for easier development
    ENABLE_HSTS = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Stricter security in production
    ENABLE_HSTS = True
    ENABLE_CSP = True
    ENABLE_XSS_PROTECTION = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Ensure secrets are set
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Validate critical configuration
        assert os.getenv('SECRET_KEY') and os.getenv('SECRET_KEY') != 'dev-secret-key-change-in-production', \
            "SECRET_KEY must be set in production"
        assert os.getenv('JWT_SECRET_KEY') and os.getenv('JWT_SECRET_KEY') != 'dev-jwt-secret-change-in-production', \
            "JWT_SECRET_KEY must be set in production"
        
        # Validate database configuration - SQLite not suitable for concurrent mobile users
        db_url = os.getenv('DATABASE_URL', '')
        assert db_url and not db_url.startswith('sqlite'), \
            "PostgreSQL required in production (SQLite not suitable for concurrent mobile users)"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False
    
    # Simple cache for tests
    CACHE_TYPE = 'simple'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
