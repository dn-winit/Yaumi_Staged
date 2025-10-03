"""
Input sanitization utilities
"""

import re
from typing import Any, Dict, List, Union


def sanitize_string(value: str, max_length: int = 255, allow_special_chars: bool = False) -> str:
    """
    Sanitize string input

    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        allow_special_chars: Whether to allow special characters

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace
    value = value.strip()

    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

    # Remove special characters if not allowed
    if not allow_special_chars:
        value = re.sub(r'[^\w\s\-_.]', '', value)

    # Limit length
    if len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_code(code: Union[str, int], alphanumeric_only: bool = True) -> str:
    """
    Sanitize code values (route codes, customer codes, item codes)

    Args:
        code: Code value to sanitize
        alphanumeric_only: Only allow alphanumeric characters

    Returns:
        Sanitized code string
    """
    code_str = str(code).strip()

    if alphanumeric_only:
        # Allow only alphanumeric and common separators
        code_str = re.sub(r'[^\w\-_]', '', code_str)
    else:
        # Remove only control characters
        code_str = ''.join(char for char in code_str if ord(char) >= 32)

    return code_str


def sanitize_dict(data: Dict[str, Any], allowed_keys: List[str] = None) -> Dict[str, Any]:
    """
    Sanitize dictionary by removing unwanted keys and sanitizing values

    Args:
        data: Dictionary to sanitize
        allowed_keys: List of allowed keys (None = allow all)

    Returns:
        Sanitized dictionary
    """
    if allowed_keys is not None:
        data = {k: v for k, v in data.items() if k in allowed_keys}

    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        clean_key = sanitize_string(key, max_length=100)

        # Sanitize value based on type
        if isinstance(value, str):
            clean_value = sanitize_string(value, allow_special_chars=True)
        elif isinstance(value, dict):
            clean_value = sanitize_dict(value, allowed_keys=None)
        elif isinstance(value, list):
            clean_value = [sanitize_string(str(item)) if isinstance(item, str) else item for item in value]
        else:
            clean_value = value

        sanitized[clean_key] = clean_value

    return sanitized
