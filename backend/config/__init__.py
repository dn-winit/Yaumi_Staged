"""
Configuration module for the backend application
"""

from .settings import (
    BASE_DIR,
    PROJECT_ROOT,
    DATA_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
    DATABASE_CONFIG,
    API_PREFIX,
    CORS_ORIGINS,
    LOG_LEVEL,
    LOG_FORMAT,
    TIER_CONFIG,
    SQL_QUERIES,
    FILE_PATTERNS,
    CACHE_SETTINGS,
    MIN_PURCHASE_HISTORY,
    MAX_DAYS_SINCE_PURCHASE,
    DEFAULT_LOOKBACK_DAYS,
    QUANTITY_PARAMS,
    NEW_CUSTOMER_PARAMS,
    get_sql_query_path,
    get_cache_file_path,
    get_output_file_path,
    get_data_file_path,
    get_config
)

__all__ = [
    'BASE_DIR',
    'PROJECT_ROOT',
    'DATA_DIR',
    'OUTPUT_DIR',
    'CACHE_DIR',
    'DATABASE_CONFIG',
    'API_PREFIX',
    'CORS_ORIGINS',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'TIER_CONFIG',
    'SQL_QUERIES',
    'FILE_PATTERNS',
    'CACHE_SETTINGS',
    'MIN_PURCHASE_HISTORY',
    'MAX_DAYS_SINCE_PURCHASE',
    'DEFAULT_LOOKBACK_DAYS',
    'QUANTITY_PARAMS',
    'NEW_CUSTOMER_PARAMS',
    'get_sql_query_path',
    'get_cache_file_path',
    'get_output_file_path',
    'get_data_file_path',
    'get_config'
]