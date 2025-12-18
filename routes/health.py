"""
Health check endpoint for monitoring and Android app connectivity
"""
from flask import Blueprint, jsonify
from datetime import datetime
from database import get_db_health

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
@health_bp.route('/api/health', methods=['GET'])  # Support both paths
def health_check():
    """
    Enhanced health check endpoint for mobile apps
    
    Returns comprehensive system status including:
    - API status
    - Database connectivity
    - Timestamp
    - API version
    - Available endpoints
    """
    # Check database health
    db_health = get_db_health()
    
    # Determine overall status
    overall_status = 'healthy' if db_health['status'] == 'connected' else 'degraded'
    
    response = {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'api_version': 'v1',
        'services': {
            'api': 'operational',
            'database': db_health['status']
        },
        'endpoints': {
            'authentication': '/api/v1/auth',
            'devices': '/api/v1/devices',
            'loans': '/api/v1/loans',
            'uploads': '/api/v1/uploads'
        }
    }
    
    # Return 503 if database is down
    status_code = 200 if overall_status == 'healthy' else 503
    
    return jsonify(response), status_code
