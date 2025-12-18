"""
Arrears Manager API - Mobile-Optimized Flask Application
Main application file with middleware integration and route registration
"""
from flask import Flask, request
from flask_cors import CORS
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os

# Import configuration
from config import get_config

# Import database
from database import init_db, db

# Import middleware
from middleware.error_handler import register_error_handlers
from middleware.security import SecurityMiddleware, configure_secure_cookies
from middleware.logging_middleware import LoggingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration name (development, production, testing)
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config = get_config(config_name)
    app.config.from_object(config)
    
    logger.info(f"Starting Arrears Manager API in {config_name} mode")
    
    # Initialize database
    init_db(app)
    
    # Initialize CORS
    CORS(app,
         origins=app.config['CORS_ORIGINS'],
         methods=app.config['CORS_METHODS'],
         allow_headers=app.config['CORS_ALLOW_HEADERS'],
         expose_headers=app.config['CORS_EXPOSE_HEADERS'],
         supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
         max_age=app.config['CORS_MAX_AGE'])
    logger.info("CORS configured for Android applications")
    
    # Initialize compression (gzip/brotli)
    Compress(app)
    logger.info("Response compression enabled")
    
    # Initialize rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['RATELIMIT_STORAGE_URL'],
        default_limits=[app.config['RATELIMIT_DEFAULT']],
        headers_enabled=app.config['RATELIMIT_HEADERS_ENABLED']
    )
    logger.info("Rate limiting configured")
    
    # Initialize security middleware
    security = SecurityMiddleware(app)
    configure_secure_cookies(app)
    logger.info("Security middleware initialized")
    
    # Initialize logging middleware
    logging_middleware = LoggingMiddleware(app)
    logger.info("Logging middleware initialized")
    
    # Register error handlers
    register_error_handlers(app)
    logger.info("Error handlers registered")
    
    # Register blueprints
    register_blueprints(app)
    
    # Create upload directory if it doesn't exist
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"Created upload folder: {upload_folder}")
    
    # Add request timeout handling
    @app.before_request
    def set_request_timeout():
        """Set request timeout for mobile optimization"""
        request.environ['werkzeug.server.shutdown_timeout'] = app.config['REQUEST_TIMEOUT']
    
    logger.info("Application initialization complete")
    
    return app


def register_blueprints(app):
    """Register all API blueprints"""
    
    # Import blueprints
    from routes.health import health_bp
    from routes.v1.auth import auth_bp
    from routes.v1.devices import devices_bp
    from routes.v1.loans import loans_bp
    from routes.v1.uploads import uploads_bp
    
    # Register health check (no version prefix)
    app.register_blueprint(health_bp)
    
    # Register v1 API blueprints
    api_prefix = f"/api/{app.config['API_VERSION']}"
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(devices_bp, url_prefix=f"{api_prefix}/devices")
    app.register_blueprint(loans_bp, url_prefix=f"{api_prefix}/loans")
    app.register_blueprint(uploads_bp, url_prefix=f"{api_prefix}/uploads")
    
    logger.info(f"API blueprints registered with prefix: {api_prefix}")


# Create application instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    port = app.config.get('PORT', 5000)
    host = app.config.get('HOST', '0.0.0.0')
    debug = app.config.get('DEBUG', False)
    
    logger.info(f"Starting development server on {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,  # Enable threading for concurrent requests
        use_reloader=debug  # Auto-reload in debug mode
    )