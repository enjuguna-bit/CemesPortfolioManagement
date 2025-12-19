"""
Test configuration and fixtures
"""
import os
import tempfile
import pytest
from flask import Flask

# Import application factory
from app import create_app
from database import db


class TestConfig:
    """Testing configuration"""
    TESTING = True
    SECRET_KEY = 'test-secret-key-do-not-use-in-production'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    
    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for most tests
    RATELIMIT_ENABLED = False
    
    # Test upload folder
    UPLOAD_FOLDER = tempfile.mkdtemp()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CORS parameters
    CORS = {
        'origins': '*',
        'methods': ['GET', 'POST', 'PUT', 'DELETE'],
        'allow_headers': ['Content-Type', 'Authorization']
    }
    
    # Config keys needed by app factory
    CORS_ORIGINS = '*'
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Device-Id']
    CORS_EXPOSE_HEADERS = []
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 600
    
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per day'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Request timeout
    REQUEST_TIMEOUT = 10
    
    API_VERSION = 'v1'
    
    # Disable external services
    FIREBASE_ENABLED = False
    REDIS_ENABLED = False


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = create_app('testing')
    app.config.from_object(TestConfig)
    
    # Override config values that might be missing in 'testing' env
    app.config.update(
        SQLALCHEMY_DATABASE_URI=TestConfig.SQLALCHEMY_DATABASE_URI,
        TESTING=True
    )
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def cleanup_upload_folder():
    """Clean up upload folder after each test"""
    yield
    
    if os.path.exists(TestConfig.UPLOAD_FOLDER):
        import shutil
        shutil.rmtree(TestConfig.UPLOAD_FOLDER, ignore_errors=True)
