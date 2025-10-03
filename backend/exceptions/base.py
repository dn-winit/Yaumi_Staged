"""
Base exception classes
"""

from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """Base exception for all API exceptions"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        result = {
            'error': self.error_code,
            'message': self.message,
            'status_code': self.status_code,
        }
        if self.details:
            result['details'] = self.details
        return result
