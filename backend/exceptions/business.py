"""
Business logic exceptions
"""

from typing import Optional, Dict, Any
from .base import BaseAPIException


class DataNotLoadedException(BaseAPIException):
    """Raised when data is not yet loaded"""
    def __init__(self, message: str = "Data not loaded yet. Please wait for data initialization."):
        super().__init__(message=message, status_code=503, error_code="DATA_NOT_LOADED")


class ValidationException(BaseAPIException):
    """Raised when validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR", details=details)


class DatabaseException(BaseAPIException):
    """Raised when database operation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, error_code="DATABASE_ERROR", details=details)


class NotFoundException(BaseAPIException):
    """Raised when resource is not found"""
    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {'resource_type': resource_type} if resource_type else None
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND", details=details)


class GenerationException(BaseAPIException):
    """Raised when generation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, error_code="GENERATION_ERROR", details=details)


class InvalidDateFormatException(ValidationException):
    """Raised when date format is invalid"""
    def __init__(self, date_value: str, expected_format: str = "YYYY-MM-DD"):
        message = f"Invalid date format: {date_value}. Expected format: {expected_format}"
        super().__init__(message=message, details={'date_value': date_value, 'expected_format': expected_format})


class MissingParametersException(ValidationException):
    """Raised when required parameters are missing"""
    def __init__(self, parameters: list):
        message = f"Missing required parameters: {', '.join(parameters)}"
        super().__init__(message=message, details={'missing_parameters': parameters})


class RouteNotFoundException(NotFoundException):
    """Raised when route is not found"""
    def __init__(self, route_code: str):
        message = f"Route not found: {route_code}"
        super().__init__(message=message, resource_type="route")


class CustomerNotFoundException(NotFoundException):
    """Raised when customer is not found"""
    def __init__(self, customer_code: str):
        message = f"Customer not found: {customer_code}"
        super().__init__(message=message, resource_type="customer")


class ItemNotFoundException(NotFoundException):
    """Raised when item is not found"""
    def __init__(self, item_code: str):
        message = f"Item not found: {item_code}"
        super().__init__(message=message, resource_type="item")
