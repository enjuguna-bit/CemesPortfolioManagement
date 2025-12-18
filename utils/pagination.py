"""
Cursor-based pagination utility for mobile-optimized API
Provides efficient pagination without offset-based performance issues
"""
import base64
import json
from typing import List, Dict, Any, Optional, Tuple
from flask import request


class PaginationCursor:
    """Cursor-based pagination helper"""
    
    @staticmethod
    def encode_cursor(data: Dict[str, Any]) -> str:
        """
        Encode cursor data to base64 string
        
        Args:
            data: Dictionary containing cursor information
        
        Returns:
            Base64-encoded cursor string
        """
        json_str = json.dumps(data, sort_keys=True)
        return base64.urlsafe_b64encode(json_str.encode()).decode()
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """
        Decode base64 cursor string to data
        
        Args:
            cursor: Base64-encoded cursor string
        
        Returns:
            Dictionary containing cursor information
        """
        try:
            json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            return json.loads(json_str)
        except Exception:
            return {}
    
    @staticmethod
    def paginate(
        items: List[Any],
        limit: int = 20,
        after_cursor: Optional[str] = None,
        before_cursor: Optional[str] = None,
        cursor_field: str = 'id'
    ) -> Dict[str, Any]:
        """
        Paginate a list of items using cursor-based pagination
        
        Args:
            items: List of items to paginate (should be sorted)
            limit: Number of items per page
            after_cursor: Cursor to get items after
            before_cursor: Cursor to get items before
            cursor_field: Field name to use for cursor
        
        Returns:
            Dictionary with paginated data and pagination metadata
        """
        # Decode cursors
        after_data = PaginationCursor.decode_cursor(after_cursor) if after_cursor else None
        before_data = PaginationCursor.decode_cursor(before_cursor) if before_cursor else None
        
        # Filter items based on cursor
        filtered_items = items
        
        if after_data and cursor_field in after_data:
            after_value = after_data[cursor_field]
            filtered_items = [
                item for item in filtered_items
                if PaginationCursor._get_field_value(item, cursor_field) > after_value
            ]
        
        if before_data and cursor_field in before_data:
            before_value = before_data[cursor_field]
            filtered_items = [
                item for item in filtered_items
                if PaginationCursor._get_field_value(item, cursor_field) < before_value
            ]
        
        # Apply limit (get one extra to check if there are more)
        has_more = len(filtered_items) > limit
        page_items = filtered_items[:limit]
        
        # Generate next cursor
        next_cursor = None
        if has_more and page_items:
            last_item = page_items[-1]
            next_cursor = PaginationCursor.encode_cursor({
                cursor_field: PaginationCursor._get_field_value(last_item, cursor_field)
            })
        
        # Generate previous cursor
        prev_cursor = None
        if page_items and (after_cursor or before_cursor):
            first_item = page_items[0]
            prev_cursor = PaginationCursor.encode_cursor({
                cursor_field: PaginationCursor._get_field_value(first_item, cursor_field)
            })
        
        return {
            'data': page_items,
            'pagination': {
                'next_cursor': next_cursor,
                'prev_cursor': prev_cursor,
                'has_more': has_more,
                'limit': limit
            }
        }
    
    @staticmethod
    def _get_field_value(item: Any, field: str) -> Any:
        """Get field value from item (supports dict and object)"""
        if isinstance(item, dict):
            return item.get(field)
        return getattr(item, field, None)


def get_pagination_params(default_limit: int = 20, max_limit: int = 100) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Extract pagination parameters from request
    
    Args:
        default_limit: Default page size
        max_limit: Maximum allowed page size
    
    Returns:
        Tuple of (limit, after_cursor, before_cursor)
    """
    # Get limit
    limit = request.args.get('limit', default_limit, type=int)
    limit = min(limit, max_limit)  # Enforce max limit
    limit = max(limit, 1)  # Ensure at least 1
    
    # Get cursors
    after_cursor = request.args.get('after')
    before_cursor = request.args.get('before')
    
    return limit, after_cursor, before_cursor


def create_pagination_response(
    items: List[Any],
    total_count: Optional[int] = None,
    limit: int = 20,
    after_cursor: Optional[str] = None,
    cursor_field: str = 'id'
) -> Dict[str, Any]:
    """
    Create standardized pagination response
    
    Args:
        items: List of items for current page
        total_count: Optional total count of all items
        limit: Page size
        after_cursor: Current cursor
        cursor_field: Field to use for cursor
    
    Returns:
        Formatted pagination response
    """
    # Check if there are more items
    has_more = len(items) > limit
    page_items = items[:limit] if has_more else items
    
    # Generate next cursor
    next_cursor = None
    if has_more and page_items:
        last_item = page_items[-1]
        cursor_value = PaginationCursor._get_field_value(last_item, cursor_field)
        next_cursor = PaginationCursor.encode_cursor({cursor_field: cursor_value})
    
    response = {
        'data': page_items,
        'pagination': {
            'next_cursor': next_cursor,
            'has_more': has_more,
            'limit': limit
        }
    }
    
    # Add total count if provided
    if total_count is not None:
        response['pagination']['total_count'] = total_count
    
    return response


def paginate_query(query, limit: int, after_cursor: Optional[str] = None, order_by_field: str = 'id'):
    """
    Paginate SQLAlchemy query using cursor-based pagination
    
    Args:
        query: SQLAlchemy query object
        limit: Number of items per page
        after_cursor: Cursor to get items after
        order_by_field: Field to order by and use for cursor
    
    Returns:
        Tuple of (items, next_cursor, has_more)
    """
    # Decode cursor
    if after_cursor:
        cursor_data = PaginationCursor.decode_cursor(after_cursor)
        if order_by_field in cursor_data:
            # Filter query based on cursor
            model = query.column_descriptions[0]['entity']
            field = getattr(model, order_by_field)
            query = query.filter(field > cursor_data[order_by_field])
    
    # Get one extra item to check if there are more
    items = query.limit(limit + 1).all()
    
    # Check if there are more items
    has_more = len(items) > limit
    page_items = items[:limit]
    
    # Generate next cursor
    next_cursor = None
    if has_more and page_items:
        last_item = page_items[-1]
        cursor_value = getattr(last_item, order_by_field)
        next_cursor = PaginationCursor.encode_cursor({order_by_field: cursor_value})
    
    return page_items, next_cursor, has_more
