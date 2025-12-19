"""
Standardized error handling middleware for mobile API
Provides consistent error response format and proper HTTP status codes
"""
from flask import jsonify, request
from werkzeug.exceptions import HTTPException
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class"""
    
    def __init__(self, message, code='API_ERROR', status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(APIError):
    """Validation error (400)"""
    def __init__(self, message, details=None):
        super().__init__(message, 'VALIDATION_ERROR', 400, details)


class AuthenticationError(APIError):
    """Authentication error (401)"""
    def __init__(self, message='Authentication required', details=None):
        super().__init__(message, 'AUTHENTICATION_ERROR', 401, details)


class AuthorizationError(APIError):
    """Authorization error (403)"""
    def __init__(self, message='Insufficient permissions', details=None):
        super().__init__(message, 'AUTHORIZATION_ERROR', 403, details)


class NotFoundError(APIError):
    """Resource not found error (404)"""
    def __init__(self, message='Resource not found', details=None):
        super().__init__(message, 'NOT_FOUND', 404, details)


class RateLimitError(APIError):
    """Rate limit exceeded error (429)"""
    def __init__(self, message='Rate limit exceeded', retry_after=None, details=None):
        super().__init__(message, 'RATE_LIMIT_EXCEEDED', 429, details)
        self.retry_after = retry_after


class ServerError(APIError):
    """Internal server error (500)"""
    def __init__(self, message='Internal server error', details=None):
        super().__init__(message, 'SERVER_ERROR', 500, details)


def format_error_response(error_code, message, details=None, correlation_id=None):
    """
    Format error response in standardized format for mobile clients
    
    Args:
        error_code: Error code string (e.g., 'VALIDATION_ERROR')
        message: Human-readable error message
        details: Optional additional error details
        correlation_id: Request correlation ID for tracing
    
    Returns:
        dict: Formatted error response
    """
    response = {
        'error': {
            'code': error_code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    if details:
        response['error']['details'] = details
    
    if correlation_id:
        response['error']['correlation_id'] = correlation_id
    
    return response


def handle_api_error(error):
    """Handle custom API errors"""
    correlation_id = getattr(request, 'correlation_id', None)
    
    response = format_error_response(
        error.code,
        error.message,
        error.details,
        correlation_id
    )
    
    # Log error with correlation ID
    logger.error(
        f"API Error: {error.code}",
        extra={
            'correlation_id': correlation_id,
            'error_code': error.code,
            'status_code': error.status_code,
            'status_code': error.status_code,
            'error_message': error.message,
            'details': error.details
        }
    )
    
    # Add Retry-After header for rate limit errors
    if isinstance(error, RateLimitError) and error.retry_after:
        return jsonify(response), error.status_code, {'Retry-After': str(error.retry_after)}
    
    return jsonify(response), error.status_code


def handle_http_exception(error):
    """Handle Werkzeug HTTP exceptions"""
    correlation_id = getattr(request, 'correlation_id', None)
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: 'BAD_REQUEST',
        401: 'AUTHENTICATION_ERROR',
        403: 'AUTHORIZATION_ERROR',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        413: 'PAYLOAD_TOO_LARGE',
        415: 'UNSUPPORTED_MEDIA_TYPE',
        429: 'RATE_LIMIT_EXCEEDED',
        500: 'SERVER_ERROR',
        502: 'BAD_GATEWAY',
        503: 'SERVICE_UNAVAILABLE',
        504: 'GATEWAY_TIMEOUT'
    }
    
    error_code = error_code_map.get(error.code, 'HTTP_ERROR')
    
    response = format_error_response(
        error_code,
        error.description or str(error),
        None,
        correlation_id
    )
    
    logger.warning(
        f"HTTP Exception: {error.code}",
        extra={
            'correlation_id': correlation_id,
            'status_code': error.code,
            'status_code': error.code,
            'error_message': error.description
        }
    )
    
    return jsonify(response), error.code


def handle_generic_exception(error):
    """Handle unexpected exceptions"""
    correlation_id = getattr(request, 'correlation_id', None)
    
    # Log full traceback for debugging
    logger.error(
        "Unexpected error",
        extra={
            'correlation_id': correlation_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
    )
    
    # Don't expose internal error details to clients in production
    from flask import current_app
    if current_app.config.get('DEBUG'):
        message = str(error)
        details = {'traceback': traceback.format_exc()}
    else:
        message = 'An unexpected error occurred'
        details = None
    
    response = format_error_response(
        'SERVER_ERROR',
        message,
        details,
        correlation_id
    )
    
    return jsonify(response), 500


def register_error_handlers(app):
    """Register all error handlers with Flask app"""
    
    # Custom API errors
    app.register_error_handler(APIError, handle_api_error)
    
    # HTTP exceptions
    app.register_error_handler(HTTPException, handle_http_exception)
    
    # Generic exceptions (catch-all)
    app.register_error_handler(Exception, handle_generic_exception)
    
    logger.info("Error handlers registered")
