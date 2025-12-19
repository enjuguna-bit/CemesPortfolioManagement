"""
Database configuration and initialization
Provides SQLAlchemy setup with connection pooling and optimization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """
    Initialize database with Flask app
    
    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy with app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Create tables if they don't exist# NOTE: Must import models before create_all() so SQLAlchemy knows about them
    with app.app_context():
        try:
            # Import all models to register them with SQLAlchemy
            import models  # noqa: F401
            
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"CRITICAL: Error creating database tables: {str(e)}")
            logger.error("Application cannot start without database. Please check database configuration.")
            raise  # Don't continue with broken database
    
    logger.info("Database initialized")


def get_db_health() -> dict:
    """
    Check database health
    
    Returns:
        Dictionary with health status
    """
    try:
        # Execute simple query to check connection
        db.session.execute(db.text('SELECT 1'))
        db.session.commit()  # Commit the test query
        return {
            'status': 'connected',
            'message': 'Database connection healthy'
        }
    except Exception as e:
        db.session.rollback()  # Clean up on error
        return {
            'status': 'disconnected',
            'message': f'Database connection failed: {str(e)}'
        }
