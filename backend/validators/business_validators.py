"""
Business logic validators
"""

from typing import List, Union
import pandas as pd

from backend.exceptions import ValidationException, RouteNotFoundException, CustomerNotFoundException, ItemNotFoundException
from .input_sanitizer import sanitize_code


def validate_route_code(route_code: Union[str, int], available_routes: pd.DataFrame = None) -> str:
    """
    Validate route code

    Args:
        route_code: Route code to validate
        available_routes: DataFrame of available routes (optional)

    Returns:
        Validated and sanitized route code

    Raises:
        ValidationException: If route code is invalid
        RouteNotFoundException: If route not found in available routes
    """
    if not route_code or (isinstance(route_code, str) and route_code.strip() == ''):
        raise ValidationException("Route code cannot be empty")

    # Sanitize
    clean_code = sanitize_code(route_code)

    # Check if exists in available routes
    if available_routes is not None and not available_routes.empty:
        if clean_code != 'All' and clean_code not in available_routes['RouteCode'].astype(str).values:
            raise RouteNotFoundException(clean_code)

    return clean_code


def validate_customer_code(customer_code: Union[str, int], available_customers: pd.DataFrame = None) -> str:
    """
    Validate customer code

    Args:
        customer_code: Customer code to validate
        available_customers: DataFrame of available customers (optional)

    Returns:
        Validated and sanitized customer code

    Raises:
        ValidationException: If customer code is invalid
        CustomerNotFoundException: If customer not found in available customers
    """
    if not customer_code or (isinstance(customer_code, str) and customer_code.strip() == ''):
        raise ValidationException("Customer code cannot be empty")

    # Sanitize
    clean_code = sanitize_code(customer_code)

    # Check if exists in available customers
    if available_customers is not None and not available_customers.empty:
        if clean_code != 'All' and clean_code not in available_customers['CustomerCode'].astype(str).values:
            raise CustomerNotFoundException(clean_code)

    return clean_code


def validate_item_code(item_code: Union[str, int], available_items: pd.DataFrame = None) -> str:
    """
    Validate item code

    Args:
        item_code: Item code to validate
        available_items: DataFrame of available items (optional)

    Returns:
        Validated and sanitized item code

    Raises:
        ValidationException: If item code is invalid
        ItemNotFoundException: If item not found in available items
    """
    if not item_code or (isinstance(item_code, str) and item_code.strip() == ''):
        raise ValidationException("Item code cannot be empty")

    # Sanitize
    clean_code = sanitize_code(item_code)

    # Check if exists in available items
    if available_items is not None and not available_items.empty:
        if clean_code != 'All' and clean_code not in available_items['ItemCode'].astype(str).values:
            raise ItemNotFoundException(clean_code)

    return clean_code
