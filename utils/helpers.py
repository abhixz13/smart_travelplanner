"""
Helper utilities for the itinerary planner system.
Common functions used across multiple modules.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique ID with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of random component
    
    Returns:
        Generated ID string
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{random_part}" if prefix else random_part


def hash_dict(data: Dict[str, Any]) -> str:
    """
    Create a hash of a dictionary for caching purposes.
    
    Args:
        data: Dictionary to hash
    
    Returns:
        MD5 hash string
    """
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(json_str.encode()).hexdigest()


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a date string into datetime object.
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        datetime object or None
    """
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code
    
    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def calculate_duration(start_date: str, end_date: str) -> int:
    """
    Calculate duration in days between two dates.
    
    Args:
        start_date: Start date string
        end_date: End date string
    
    Returns:
        Number of days
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if not start or not end:
        return 0
    
    return (end - start).days


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate that date range is logical.
    
    Args:
        start_date: Start date string
        end_date: End date string
    
    Returns:
        True if valid, False otherwise
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if not start or not end:
        return False
    
    return end >= start


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple dictionaries.
    
    Args:
        *dicts: Variable number of dictionaries
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
    return result


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text (simple implementation).
    
    Args:
        text: Text to analyze
        min_length: Minimum keyword length
    
    Returns:
        List of keywords
    """
    # Simple keyword extraction (in production, use NLP libraries)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}
    
    words = text.lower().split()
    keywords = [w.strip('.,!?;:') for w in words 
                if len(w) >= min_length and w.lower() not in stop_words]
    
    return list(set(keywords))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    return sanitized


def retry_with_backoff(func, max_retries: int = 3, initial_delay: float = 1.0):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
    
    Returns:
        Function result
    
    Raises:
        Last exception if all retries fail
    """
    import time
    
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise last_exception


def calculate_budget_per_day(total_budget: float, duration_days: int, 
                            allocations: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Calculate budget allocation per day and category.
    
    Args:
        total_budget: Total trip budget
        duration_days: Trip duration in days
        allocations: Optional category allocation percentages
    
    Returns:
        Budget breakdown dictionary
    """
    if not allocations:
        # Default allocation percentages
        allocations = {
            "accommodation": 0.35,
            "food": 0.25,
            "activities": 0.25,
            "transportation": 0.10,
            "miscellaneous": 0.05
        }
    
    daily_budget = total_budget / duration_days if duration_days > 0 else 0
    
    breakdown = {
        "total_budget": total_budget,
        "duration_days": duration_days,
        "daily_budget": daily_budget,
        "categories": {}
    }
    
    for category, percentage in allocations.items():
        breakdown["categories"][category] = {
            "daily": daily_budget * percentage,
            "total": total_budget * percentage
        }
    
    return breakdown


def validate_email(email: str) -> bool:
    """
    Simple email validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return bool(re.match(pattern, email))


def time_ago(dt: datetime) -> str:
    """
    Convert datetime to human-readable "time ago" string.
    
    Args:
        dt: Datetime object
    
    Returns:
        Human-readable string (e.g., "2 hours ago")
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate list of dates between start and end.
    
    Args:
        start_date: Start date string
        end_date: End date string
    
    Returns:
        List of date strings
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if not start or not end:
        return []
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates


def estimate_travel_time(distance_km: float, mode: str = "car") -> Dict[str, Any]:
    """
    Estimate travel time based on distance and mode.
    
    Args:
        distance_km: Distance in kilometers
        mode: Transportation mode (car, train, flight, walk)
    
    Returns:
        Estimated duration dictionary
    """
    # Average speeds in km/h
    speeds = {
        "walk": 5,
        "bike": 15,
        "car": 60,
        "train": 80,
        "flight": 500
    }
    
    speed = speeds.get(mode.lower(), 50)
    hours = distance_km / speed
    
    return {
        "distance_km": distance_km,
        "mode": mode,
        "hours": hours,
        "formatted": f"{int(hours)}h {int((hours % 1) * 60)}m"
    }


class ResponseFormatter:
    """Helper class for formatting responses consistently."""
    
    @staticmethod
    def success(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format success response."""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(error: str, code: str = "ERROR") -> Dict[str, Any]:
        """Format error response."""
        return {
            "success": False,
            "error": error,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def paginated(items: List[Any], page: int, per_page: int, 
                  total: int) -> Dict[str, Any]:
        """Format paginated response."""
        return {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }


# Example usage documentation
if __name__ == "__main__":
    # Test helper functions
    print("Testing helper functions...")
    
    # Test date parsing
    date = parse_date("2025-06-01")
    print(f"Parsed date: {date}")
    
    # Test currency formatting
    amount = format_currency(1234.56)
    print(f"Formatted: {amount}")
    
    # Test budget calculation
    budget = calculate_budget_per_day(5000, 7)
    print(f"Budget breakdown: {budget}")
    
    # Test ID generation
    id = generate_id("TRIP_", 8)
    print(f"Generated ID: {id}")
    
    print("\nAll helper functions loaded successfully!")