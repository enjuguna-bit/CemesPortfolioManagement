"""
Test configuration and fixtures
"""
import os
import tempfile
import pytest
from flask import Flask


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
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000']
    
    # Disable external services
    FIREBASE_ENABLED = False
    REDIS_ENABLED = False


@pytest.fixture(scope='session')
def test_config():
    """Provide test configuration"""
    return TestConfig


@pytest.fixture(autouse=True)
def cleanup_upload_folder():
    """Clean up upload folder after each test"""
    yield
    
    if os.path.exists(TestConfig.UPLOAD_FOLDER):
        import shutil
        shutil.rmtree(TestConfig.UPLOAD_FOLDER, ignore_errors=True)
