"""
Security middleware for mobile API
Implements HTTPS enforcement, security headers, and protection against common attacks
"""
from flask import request, make_response
from functools import wraps
import re
import logging

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Security middleware for Flask application"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware"""
        self.app = app
        
        # Register before_request and after_request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        logger.info("Security middleware initialized")
    
    def before_request(self):
        """Run security checks before each request"""
        # HTTPS enforcement (in production)
        if self.app.config.get('ENABLE_HSTS') and not request.is_secure:
            if not self.app.config.get('DEBUG'):
                from middleware.error_handler import ValidationError
                raise ValidationError('HTTPS required')
        
        # SQL injection pattern detection (basic)
        self._check_sql_injection()
        
        # XSS pattern detection (basic)
        self._check_xss()
    
    def after_request(self, response):
        """Add security headers to response"""
        
        # HSTS (HTTP Strict Transport Security)
        if self.app.config.get('ENABLE_HSTS'):
            max_age = self.app.config.get('HSTS_MAX_AGE', 31536000)
            response.headers['Strict-Transport-Security'] = f'max-age={max_age}; includeSubDomains'
        
        # Content Security Policy
        if self.app.config.get('ENABLE_CSP'):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        
        # XSS Protection
        if self.app.config.get('ENABLE_XSS_PROTECTION'):
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Frame options (prevent clickjacking)
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature-Policy)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=()'
        )
        
        # Remove server header to avoid information disclosure
        response.headers.pop('Server', None)
        
        # Add correlation ID to response
        if hasattr(request, 'correlation_id'):
            response.headers['X-Correlation-Id'] = request.correlation_id
        
        return response
    
    def _check_sql_injection(self):
        """Basic SQL injection pattern detection"""
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(--|\#|\/\*)",
            r"(\bor\b.*=.*)",
            r"(\band\b.*=.*)"
        ]
        
        # Check query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value.lower()):
                        logger.warning(
                            f"Potential SQL injection detected in query param: {key}",
                            extra={'param': key, 'value': value[:100]}
                        )
                        from middleware.error_handler import ValidationError
                        raise ValidationError('Invalid input detected')
        
        # Check JSON body
        if request.is_json:
            self._check_dict_for_sql_injection(request.get_json(silent=True) or {}, sql_patterns)
    
    def _check_dict_for_sql_injection(self, data, patterns):
        """Recursively check dictionary for SQL injection patterns"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    for pattern in patterns:
                        if re.search(pattern, value.lower()):
                            logger.warning(
                                f"Potential SQL injection detected in JSON field: {key}",
                                extra={'field': key, 'value': value[:100]}
                            )
                            from middleware.error_handler import ValidationError
                            raise ValidationError('Invalid input detected')
                elif isinstance(value, (dict, list)):
                    self._check_dict_for_sql_injection(value, patterns)
        elif isinstance(data, list):
            for item in data:
                self._check_dict_for_sql_injection(item, patterns)
    
    def _check_xss(self):
        """Basic XSS pattern detection"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"onclick\s*="
        ]
        
        # Check query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value.lower()):
                        logger.warning(
                            f"Potential XSS detected in query param: {key}",
                            extra={'param': key, 'value': value[:100]}
                        )
                        from middleware.error_handler import ValidationError
                        raise ValidationError('Invalid input detected')


def configure_secure_cookies(app):
    """Configure secure cookie settings"""
    app.config.update(
        SESSION_COOKIE_SECURE=not app.config.get('DEBUG'),  # HTTPS only in production
        SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access
        SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
        PERMANENT_SESSION_LIFETIME=3600  # 1 hour
    )
    
    logger.info("Secure cookie settings configured")


def sanitize_input(value):
    """
    Sanitize user input to prevent XSS and injection attacks
    
    Args:
        value: Input value to sanitize
    
    Returns:
        Sanitized value
    """
    if not isinstance(value, str):
        return value
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    sanitized = value
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def require_https(f):
    """Decorator to require HTTPS for specific endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not request.app.config.get('DEBUG'):
            from middleware.error_handler import ValidationError
            raise ValidationError('HTTPS required for this endpoint')
        return f(*args, **kwargs)
    return decorated_function
