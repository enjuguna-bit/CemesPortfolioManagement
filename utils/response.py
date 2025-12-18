"""
Response utilities for mobile-optimized API
Includes standardized responses, caching, compression, and partial field selection
"""
from flask import jsonify, request, make_response
from datetime import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> tuple:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code
        headers: Optional additional headers
    
    Returns:
        Tuple of (response, status_code, headers)
    """
    response_data = {
        'success': True,
        'data': data,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if message:
        response_data['message'] = message
    
    # Add correlation ID if available
    if hasattr(request, 'correlation_id'):
        response_data['correlation_id'] = request.correlation_id
    
    response = jsonify(response_data)
    
    # Add custom headers
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    
    return response, status_code


def generate_etag(data: Any) -> str:
    """
    Generate ETag for response data
    
    Args:
        data: Response data
    
    Returns:
        ETag string
    """
    # Convert data to JSON string
    json_str = json.dumps(data, sort_keys=True, default=str)
    
    # Generate hash
    etag = hashlib.md5(json_str.encode()).hexdigest()
    
    return f'"{etag}"'


def check_etag(data: Any) -> bool:
    """
    Check if client's ETag matches current data
    
    Args:
        data: Current response data
    
    Returns:
        True if ETag matches (304 should be returned)
    """
    client_etag = request.headers.get('If-None-Match')
    
    if not client_etag:
        return False
    
    current_etag = generate_etag(data)
    
    return client_etag == current_etag


def cached_response(
    data: Any,
    max_age: int = 300,
    private: bool = False,
    must_revalidate: bool = True
) -> tuple:
    """
    Create response with caching headers
    
    Args:
        data: Response data
        max_age: Cache max age in seconds
        private: Whether cache is private (user-specific)
        must_revalidate: Whether cache must revalidate
    
    Returns:
        Response tuple
    """
    # Check ETag
    if check_etag(data):
        # Return 304 Not Modified
        response = make_response('', 304)
        response.headers['ETag'] = generate_etag(data)
        return response, 304
    
    # Create success response
    response, status_code = success_response(data)
    
    # Add ETag
    etag = generate_etag(data)
    response.headers['ETag'] = etag
    
    # Add Cache-Control header
    cache_directives = []
    
    if private:
        cache_directives.append('private')
    else:
        cache_directives.append('public')
    
    cache_directives.append(f'max-age={max_age}')
    
    if must_revalidate:
        cache_directives.append('must-revalidate')
    
    response.headers['Cache-Control'] = ', '.join(cache_directives)
    
    # Add Last-Modified header
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response, status_code


def select_fields(data: Any, fields: Optional[List[str]] = None) -> Any:
    """
    Select specific fields from response data (sparse fieldsets)
    
    Args:
        data: Response data (dict or list of dicts)
        fields: List of field names to include
    
    Returns:
        Filtered data with only requested fields
    """
    if not fields:
        return data
    
    if isinstance(data, dict):
        return {key: value for key, value in data.items() if key in fields}
    
    if isinstance(data, list):
        return [
            {key: value for key, value in item.items() if key in fields}
            if isinstance(item, dict) else item
            for item in data
        ]
    
    return data


def get_requested_fields() -> Optional[List[str]]:
    """
    Get requested fields from query parameters
    
    Returns:
        List of field names or None
    """
    fields_param = request.args.get('fields')
    
    if not fields_param:
        return None
    
    # Split by comma and strip whitespace
    return [field.strip() for field in fields_param.split(',')]


def partial_response(data: Any, **kwargs) -> tuple:
    """
    Create response with partial field selection support
    
    Args:
        data: Response data
        **kwargs: Additional arguments for success_response
    
    Returns:
        Response tuple
    """
    # Get requested fields
    fields = get_requested_fields()
    
    # Filter data if fields specified
    if fields:
        # Handle pagination response
        if isinstance(data, dict) and 'data' in data:
            filtered_data = data.copy()
            filtered_data['data'] = select_fields(data['data'], fields)
        else:
            filtered_data = select_fields(data, fields)
    else:
        filtered_data = data
    
    return success_response(filtered_data, **kwargs)


def add_response_headers(response, headers: Dict[str, str]):
    """
    Add multiple headers to response
    
    Args:
        response: Flask response object
        headers: Dictionary of headers to add
    
    Returns:
        Modified response
    """
    for key, value in headers.items():
        response.headers[key] = value
    
    return response


def compress_response(response, min_size: int = 500):
    """
    Compress response if size exceeds threshold
    Note: Flask-Compress handles this automatically, this is for manual control
    
    Args:
        response: Flask response object
        min_size: Minimum size in bytes to compress
    
    Returns:
        Potentially compressed response
    """
    # Check if response is large enough to compress
    if response.content_length and response.content_length < min_size:
        return response
    
    # Check if client accepts compression
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    if 'br' in accept_encoding:
        # Brotli compression (better for mobile)
        import brotli
        compressed = brotli.compress(response.get_data())
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'br'
    elif 'gzip' in accept_encoding:
        # Gzip compression
        import gzip
        compressed = gzip.compress(response.get_data())
        response.set_data(compressed)
        response.headers['Content-Encoding'] = 'gzip'
    
    return response


def mobile_optimized_response(
    data: Any,
    cacheable: bool = False,
    max_age: int = 300,
    **kwargs
) -> tuple:
    """
    Create mobile-optimized response with all optimizations
    
    Args:
        data: Response data
        cacheable: Whether response should be cached
        max_age: Cache max age in seconds
        **kwargs: Additional arguments
    
    Returns:
        Optimized response tuple
    """
    # Apply field selection
    fields = get_requested_fields()
    if fields:
        if isinstance(data, dict) and 'data' in data:
            filtered_data = data.copy()
            filtered_data['data'] = select_fields(data['data'], fields)
        else:
            filtered_data = select_fields(data, fields)
    else:
        filtered_data = data
    
    # Create response with caching if enabled
    if cacheable:
        return cached_response(filtered_data, max_age=max_age)
    else:
        return success_response(filtered_data, **kwargs)
