"""
Enumerations for the application
"""

from enum import Enum


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class PeriodType(str, Enum):
    """Period aggregation types"""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class TierType(str, Enum):
    """Recommendation tiers"""
    MUST_STOCK = "MUST_STOCK"
    SHOULD_STOCK = "SHOULD_STOCK"
    CONSIDER = "CONSIDER"
    MONITOR = "MONITOR"
    EXCLUDE = "EXCLUDE"
    NEW_CUSTOMER = "NEW_CUSTOMER"
    MULTIPLE = "MULTIPLE"


class StrategyType(str, Enum):
    """Priority calculation strategies"""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DataSource(str, Enum):
    """Data source types"""
    LOADED = "loaded"
    GENERATED = "generated"
    CACHED = "cached"
