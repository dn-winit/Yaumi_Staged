"""
Centralized configuration for the backend application
All paths are dynamically generated - no hardcoding
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base paths - dynamically determined
BASE_DIR = Path(__file__).resolve().parent.parent  # backend directory
PROJECT_ROOT = BASE_DIR.parent  # webapp directory
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
CACHE_DIR = DATA_DIR / 'cache'

# Ensure directories exist
for directory in [DATA_DIR, OUTPUT_DIR, CACHE_DIR, OUTPUT_DIR / 'recommendations', OUTPUT_DIR / 'supervision']:
    directory.mkdir(parents=True, exist_ok=True)

# Database configuration - ALL VALUES FROM ENVIRONMENT VARIABLES
DATABASE_CONFIG = {
    'DRIVER': os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}'),
    'SERVER': os.getenv('DB_SERVER'),
    'DATABASE': os.getenv('DB_NAME'),
    'UID': os.getenv('DB_USER'),
    'PWD': os.getenv('DB_PASSWORD')
}

# API Configuration
API_PREFIX = os.getenv('API_PREFIX', '/api/v1')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Recommendation System Configuration - Updated to match legacy system
# Legacy tier configuration (kept for compatibility)
TIER_CONFIG = {
    'MUST_STOCK': {
        'prob_min': 0.60,
        'urgency_min': 70,
        'qty_factor': 1.00
    },
    'SHOULD_STOCK': {
        'prob_min': 0.40,
        'urgency_min': 50,
        'qty_factor': 0.80
    },
    'CONSIDER': {
        'prob_min': 0.25,
        'urgency_min': 30,
        'qty_factor': 0.60
    },
    'MONITOR': {
        'prob_min': 0.15,
        'urgency_min': 20,
        'qty_factor': 0.40
    }
}

# Processing parameters
MIN_PURCHASE_HISTORY = 3
MAX_DAYS_SINCE_PURCHASE = 365
DEFAULT_LOOKBACK_DAYS = 180

# Quantity calculation parameters
QUANTITY_PARAMS = {
    'OVERDUE_MULTIPLIER': 1.1,
    'MAX_QTY_MULTIPLIER': 1.2,
    'MIN_QTY_FACTORS': {
        'MUST_STOCK': 0.5,
        'SHOULD_STOCK': 0.3
    },
    'NEW_CUSTOMER_QTY': 5,
    'NEW_CUSTOMER_ITEMS_COUNT': 5
}

# New customer parameters
NEW_CUSTOMER_PARAMS = {
    'TIER': 'NEW_CUSTOMER',
    'PROBABILITY_PERCENT': 25.0,
    'URGENCY_SCORE': 25.0,
    'AVG_QUANTITY': 5,
    'FREQUENCY_PERCENT': 0.0,
    'DAYS_SINCE_LAST': 0,
    'CYCLE_DAYS': 0
}

# SQL Query Configuration
SQL_QUERIES = {
    'demand_data': 'demand_data.sql',
    'recent_demand': 'recent_demand.sql',
    'customer_data': 'customer_data.sql',
    'journey_plan': 'journey_plan.sql'
}

# File naming patterns
FILE_PATTERNS = {
    'recommendation': 'rec_{route_code}_{date}.csv',
    'supervision_visit': 'visit_{session_key}_{customer}_{timestamp}.json',
    'supervision_report': 'report_{session_key}_{timestamp}.json'
}

# Cache settings
CACHE_SETTINGS = {
    'enabled': True,
    'ttl_seconds': 3600,  # 1 hour
    'max_size_mb': 100
}

def get_sql_query_path(query_name: str) -> Path:
    """Get the path to a SQL query file"""
    # First try to find it in the project structure
    possible_paths = [
        PROJECT_ROOT / 'sql' / SQL_QUERIES.get(query_name, query_name),
        BASE_DIR / 'sql' / SQL_QUERIES.get(query_name, query_name),
        DATA_DIR / 'sql' / SQL_QUERIES.get(query_name, query_name),
    ]
    
    # Also check if there's an external data source
    external_data_path = Path(os.getenv('EXTERNAL_DATA_PATH', PROJECT_ROOT.parent / 'recommended_order'))
    if external_data_path.exists():
        possible_paths.append(external_data_path / 'data' / 'sql' / SQL_QUERIES.get(query_name, query_name))
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return the first path as default
    return possible_paths[0]

def get_cache_file_path(filename: str) -> Path:
    """Get the path to a cache file"""
    return CACHE_DIR / filename

def get_output_file_path(category: str, filename: str) -> Path:
    """Get the path to an output file"""
    category_dir = OUTPUT_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    return category_dir / filename

def get_data_file_path(filename: str) -> Path:
    """Get the path to a data file"""
    return DATA_DIR / filename

# Export configuration as a dictionary
def get_config() -> Dict[str, Any]:
    """Get the complete configuration as a dictionary"""
    return {
        'database': DATABASE_CONFIG,
        'api': {
            'prefix': API_PREFIX,
            'cors_origins': CORS_ORIGINS
        },
        'paths': {
            'base_dir': str(BASE_DIR),
            'project_root': str(PROJECT_ROOT),
            'data_dir': str(DATA_DIR),
            'output_dir': str(OUTPUT_DIR),
            'cache_dir': str(CACHE_DIR)
        },
        'logging': {
            'level': LOG_LEVEL,
        },
        'tiers': TIER_CONFIG,
        'cache': CACHE_SETTINGS,
        'environment': ENVIRONMENT
    }


def validate_config() -> Dict[str, Any]:
    """
    Validate configuration settings

    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []

    # Validate database configuration
    for key in ['DRIVER', 'SERVER', 'DATABASE', 'UID', 'PWD']:
        if not DATABASE_CONFIG.get(key):
            issues.append(f"Missing database configuration: {key}")

    # Validate directories exist
    for dir_path in [DATA_DIR, OUTPUT_DIR, CACHE_DIR]:
        if not dir_path.exists():
            warnings.append(f"Directory does not exist (will be created): {dir_path}")

    # Validate log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOG_LEVEL not in valid_log_levels:
        issues.append(f"Invalid LOG_LEVEL: {LOG_LEVEL}. Must be one of {valid_log_levels}")

    # Validate environment
    valid_environments = ['development', 'staging', 'production']
    if ENVIRONMENT not in valid_environments:
        warnings.append(f"Unusual ENVIRONMENT value: {ENVIRONMENT}")

    # Validate secret key in production
    if ENVIRONMENT == 'production' and SECRET_KEY == 'dev-secret-key-change-in-production':
        issues.append("SECRET_KEY must be changed in production environment")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }