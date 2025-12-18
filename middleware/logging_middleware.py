"""
Structured logging middleware with correlation IDs and request tracing
Provides JSON-formatted logs with device information and sensitive data redaction
"""
from flask import request, g
import logging
import json
import uuid
from datetime import datetime
import time

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


class StructuredLogger(logging.Logger):
    """Custom logger that outputs JSON-formatted logs"""
    
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        """Override _log to format as JSON"""
        if extra is None:
            extra = {}
        
        # Build log record
        record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': logging.getLevelName(level),
            'message': msg,
            **extra
        }
        
        # Add exception info if present
        if exc_info:
            import traceback
            record['exception'] = ''.join(traceback.format_exception(*exc_info))
        
        # Output as JSON
        super()._log(level, json.dumps(record), args, exc_info, extra, stack_info)


class LoggingMiddleware:
    """Logging middleware for request/response tracking"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('api')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logging middleware"""
        self.app = app
        
        # Register before_request and after_request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        self.logger.info("Logging middleware initialized")
    
    def before_request(self):
        """Log request start and generate correlation ID"""
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-Id') or str(uuid.uuid4())
        request.correlation_id = correlation_id
        g.correlation_id = correlation_id
        
        # Store request start time
        g.request_start_time = time.time()
        
        # Extract device information
        device_id = request.headers.get('X-Device-Id')
        device_platform = request.headers.get('X-Device-Platform', 'unknown')
        app_version = request.headers.get('X-App-Version', 'unknown')
        
        # Log request
        self.logger.info(
            "Request started",
            extra={
                'correlation_id': correlation_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'device_id': device_id,
                'device_platform': device_platform,
                'app_version': app_version,
                'content_length': request.content_length
            }
        )
    
    def after_request(self, response):
        """Log request completion"""
        if not hasattr(g, 'request_start_time'):
            return response
        
        # Calculate request duration
        duration = time.time() - g.request_start_time
        
        # Get user ID if authenticated
        user_id = getattr(g, 'user_id', None)
        
        # Log response
        self.logger.info(
            "Request completed",
            extra={
                'correlation_id': getattr(request, 'correlation_id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'response_size': response.content_length,
                'user_id': user_id
            }
        )
        
        return response
    
    def teardown_request(self, exception=None):
        """Log request errors"""
        if exception:
            self.logger.error(
                "Request failed with exception",
                extra={
                    'correlation_id': getattr(request, 'correlation_id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception)
                },
                exc_info=True
            )
    
    def _get_client_ip(self):
        """Get client IP address (handles proxies)"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr


def redact_sensitive_data(data, sensitive_fields=None):
    """
    Redact sensitive data from logs
    
    Args:
        data: Dictionary or object to redact
        sensitive_fields: List of field names to redact
    
    Returns:
        Redacted data
    """
    if sensitive_fields is None:
        sensitive_fields = [
            'password', 'token', 'secret', 'api_key', 'authorization',
            'credit_card', 'ssn', 'pin', 'cvv'
        ]
    
    if not isinstance(data, dict):
        return data
    
    redacted = data.copy()
    
    for key, value in redacted.items():
        # Check if field should be redacted
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            redacted[key] = '***REDACTED***'
        # Recursively redact nested dictionaries
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value, sensitive_fields)
        # Redact lists of dictionaries
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            redacted[key] = [redact_sensitive_data(item, sensitive_fields) for item in value]
    
    return redacted


def log_api_call(endpoint, user_id=None, **kwargs):
    """
    Log API call with structured data
    
    Args:
        endpoint: API endpoint name
        user_id: Optional user ID
        **kwargs: Additional log data
    """
    logger = logging.getLogger('api')
    
    log_data = {
        'correlation_id': getattr(request, 'correlation_id', 'unknown'),
        'endpoint': endpoint,
        'user_id': user_id,
        **kwargs
    }
    
    # Redact sensitive data
    log_data = redact_sensitive_data(log_data)
    
    logger.info(f"API call: {endpoint}", extra=log_data)
