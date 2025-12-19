"""
Input validation utilities for mobile API
Provides file validation, schema validation, and security checks
"""
from flask import request
from werkzeug.datastructures import FileStorage
from middleware.error_handler import ValidationError
from typing import List, Dict, Any, Optional
import re
import os


def validate_file(
    file: FileStorage,
    allowed_extensions: Optional[List[str]] = None,
    max_size: Optional[int] = None,
    required: bool = True
) -> bool:
    """
    Validate uploaded file
    
    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed file extensions
        max_size: Maximum file size in bytes
        required: Whether file is required
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If validation fails
    """
    if not file or file.filename == '':
        if required:
            raise ValidationError('No file provided', details={'field': 'file'})
        return False
    
    # Check file extension
    if allowed_extensions:
        ext = get_file_extension(file.filename)
        # Allow empty extension if we want to be very lenient, or just log it
        if ext not in allowed_extensions:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"File validation failed. Filename: '{file.filename}', Extracted extension: '{ext}', Allowed: {allowed_extensions}")
            
            raise ValidationError(
                f"Invalid file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
                details={'field': 'file', 'filename': file.filename, 'extension': ext}
            )
    
    # Check file size
    if max_size:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValidationError(
                f'File too large. Maximum size: {max_mb:.1f}MB',
                details={'field': 'file'}
            )
    
    return True


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: File name
    
    Returns:
        File extension (lowercase, without dot)
    """
    if '.' not in filename:
        return ''
    
    return filename.rsplit('.', 1)[1].lower()


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If invalid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError('Invalid email address format', details={'field': 'email'})
    
    return True


def validate_phone(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number
        country_code: Optional country code for specific validation
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If invalid
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Basic validation: should be digits and optional + at start
    if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
        raise ValidationError('Invalid phone number format', details={'field': 'phone'})
    
    return True


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that required fields are present
    
    Args:
        data: Data dictionary
        required_fields: List of required field names
    
    Returns:
        True if all required fields present
    
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            f'Missing required fields: {", ".join(missing_fields)}'
        )
    
    return True


def validate_string_length(
    value: str,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> bool:
    """
    Validate string length
    
    Args:
        value: String value
        field_name: Field name for error message
        min_length: Minimum length
        max_length: Maximum length
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If invalid
    """
    if min_length and len(value) < min_length:
        raise ValidationError(
            f'{field_name} must be at least {min_length} characters',
            details={'field': field_name}
        )
    
    if max_length and len(value) > max_length:
        raise ValidationError(
            f'{field_name} must be at most {max_length} characters',
            details={'field': field_name}
        )
    
    return True


def validate_numeric_range(
    value: float,
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> bool:
    """
    Validate numeric value range
    
    Args:
        value: Numeric value
        field_name: Field name for error message
        min_value: Minimum value
        max_value: Maximum value
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If invalid
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f'{field_name} must be at least {min_value}',
            details={'field': field_name}
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f'{field_name} must be at most {max_value}',
            details={'field': field_name}
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate JSON data against schema
    
    Args:
        data: Data to validate
        schema: Schema definition
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If validation fails
    """
    # Simple schema validation (can be extended with jsonschema library)
    for field, rules in schema.items():
        # Check required
        if rules.get('required') and field not in data:
            raise ValidationError(f'Missing required field: {field}', details={'field': field})
        
        if field not in data:
            continue
        
        value = data[field]
        
        # Check type
        expected_type = rules.get('type')
        if expected_type:
            type_map = {
                'string': str,
                'number': (int, float),
                'integer': int,
                'boolean': bool,
                'array': list,
                'object': dict
            }
            
            if expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    raise ValidationError(
                        f'{field} must be of type {expected_type}',
                        details={'field': field}
                    )
        
        # Check string length
        if isinstance(value, str):
            if 'min_length' in rules:
                validate_string_length(value, field, min_length=rules['min_length'])
            if 'max_length' in rules:
                validate_string_length(value, field, max_length=rules['max_length'])
        
        # Check numeric range
        if isinstance(value, (int, float)):
            if 'min' in rules:
                validate_numeric_range(value, field, min_value=rules['min'])
            if 'max' in rules:
                validate_numeric_range(value, field, max_value=rules['max'])
        
        # Check enum
        if 'enum' in rules and value not in rules['enum']:
            raise ValidationError(
                f'{field} must be one of: {", ".join(map(str, rules["enum"]))}',
                details={'field': field}
            )
    
    return True


def validate_idempotency_key(key: Optional[str] = None) -> Optional[str]:
    """
    Validate and extract idempotency key from request
    
    Args:
        key: Optional key to validate (if not provided, extracted from headers)
    
    Returns:
        Validated idempotency key or None
    """
    if key is None:
        key = request.headers.get('X-Idempotency-Key')
    
    if not key:
        return None
    
    # Validate format (UUID-like)
    if not re.match(r'^[a-zA-Z0-9\-_]{16,128}$', key):
        raise ValidationError('Invalid idempotency key format')
    
    return key
