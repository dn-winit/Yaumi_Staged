"""
Date validation utilities
"""

from datetime import datetime, date
from typing import Tuple, Optional
import pandas as pd

from backend.exceptions import InvalidDateFormatException, ValidationException
from backend.constants.config_constants import DATE_FORMAT


def parse_date(date_string: str, formats: Optional[list] = None) -> datetime:
    """
    Parse date string with multiple format support

    Args:
        date_string: Date string to parse
        formats: List of formats to try (default: ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'])

    Returns:
        datetime object

    Raises:
        InvalidDateFormatException: If date cannot be parsed
    """
    if formats is None:
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y%m%d']

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise InvalidDateFormatException(date_string, expected_format=" or ".join(formats))


def validate_date(date_value: str, min_date: Optional[date] = None, max_date: Optional[date] = None) -> datetime:
    """
    Validate and parse date with optional range check

    Args:
        date_value: Date string to validate
        min_date: Minimum allowed date
        max_date: Maximum allowed date

    Returns:
        Validated datetime object

    Raises:
        InvalidDateFormatException: If date format is invalid
        ValidationException: If date is out of range
    """
    parsed_date = parse_date(date_value)

    if min_date and parsed_date.date() < min_date:
        raise ValidationException(
            f"Date {date_value} is before minimum allowed date {min_date}",
            details={'date': date_value, 'min_date': str(min_date)}
        )

    if max_date and parsed_date.date() > max_date:
        raise ValidationException(
            f"Date {date_value} is after maximum allowed date {max_date}",
            details={'date': date_value, 'max_date': str(max_date)}
        )

    return parsed_date


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """
    Validate date range

    Args:
        start_date: Start date string
        end_date: End date string

    Returns:
        Tuple of (start_datetime, end_datetime)

    Raises:
        ValidationException: If end_date is before start_date
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    if end_dt < start_dt:
        raise ValidationException(
            f"End date {end_date} cannot be before start date {start_date}",
            details={'start_date': start_date, 'end_date': end_date}
        )

    return start_dt, end_dt
