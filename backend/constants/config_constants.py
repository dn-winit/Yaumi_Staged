"""
Configuration constants
"""

# Database
DATABASE_CONNECTION_TIMEOUT = 30
DATABASE_RETRY_ATTEMPTS = 3
DATABASE_RETRY_DELAY = 2

# API
DEFAULT_API_PREFIX = '/api/v1'
API_VERSION = '2.0.0'
API_TITLE = 'Yaumi Analytics API'
API_DESCRIPTION = 'Professional Analytics Platform for Yaumi - Demand, Forecast, Recommendations & Supervision'

# Cache
DEFAULT_CACHE_TTL = 3600  # 1 hour
DEFAULT_CACHE_MAX_SIZE_MB = 100

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Recommendation System
MIN_PRIORITY_THRESHOLD = 15
DEFAULT_NEW_CUSTOMER_QTY = 5
DEFAULT_NEW_CUSTOMER_ITEMS_COUNT = 5
MAX_DAYS_SINCE_PURCHASE_DEFAULT = 365
MIN_PURCHASE_HISTORY_DEFAULT = 3
DEFAULT_LOOKBACK_DAYS = 180

# Priority Weights
PRIORITY_WEIGHTS = {
    'purchase_pattern': 0.45,
    'timing_need': 0.35,
    'customer_value': 0.20
}

# Customer Value Weights
CUSTOMER_VALUE_WEIGHTS = {
    'size': 0.50,
    'importance': 0.25,
    'activity': 0.15,
    'growth': 0.10
}

# Logging
LOG_FORMAT_DETAILED = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
LOG_FORMAT_SIMPLE = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Request/Response
REQUEST_TIMEOUT = 120  # seconds
MAX_REQUEST_SIZE_MB = 10

# Security
SESSION_MAX_AGE = 3600  # 1 hour
ALLOWED_HOSTS_PRODUCTION = ["*.onrender.com", "*.vercel.app", "yaumi.com", "*.yaumi.com"]

# File naming
FILE_DATE_FORMAT = '%Y%m%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
