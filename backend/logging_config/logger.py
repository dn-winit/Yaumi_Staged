"""
Production-grade logging configuration with rotation and structured logging
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from backend.constants.config_constants import (
    LOG_FORMAT_DETAILED,
    LOG_FORMAT_SIMPLE,
    LOG_DATE_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT
)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter to add contextual information to log records
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra fields to the log record"""
        extra = kwargs.get('extra', {})

        # Add context from adapter
        if self.extra:
            extra.update(self.extra)

        kwargs['extra'] = {'extra_fields': extra}
        return msg, kwargs


def setup_logging(
    log_level: str = 'INFO',
    log_dir: Optional[Path] = None,
    app_name: str = 'winit_analytics',
    json_logs: bool = False,
    console_output: bool = True
) -> None:
    """
    Setup application-wide logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = no file logging)
        app_name: Application name for log files
        json_logs: Use JSON formatting for structured logs
        console_output: Enable console output
    """

    # Convert log level string to constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if json_logs:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt=LOG_FORMAT_DETAILED,
            datefmt=LOG_DATE_FORMAT
        )

    simple_formatter = logging.Formatter(
        fmt=LOG_FORMAT_SIMPLE,
        datefmt=LOG_DATE_FORMAT
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter if not json_logs else formatter)
        root_logger.addHandler(console_handler)

    # File handlers with rotation
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main application log with rotation
        app_log_file = log_dir / f'{app_name}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Error log (only errors and above)
        error_log_file = log_dir / f'{app_name}_error.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Daily rotating log
        daily_log_file = log_dir / f'{app_name}_daily.log'
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        daily_handler.setLevel(numeric_level)
        daily_handler.setFormatter(formatter)
        root_logger.addHandler(daily_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    root_logger.info(f"Logging configured: level={log_level}, json_logs={json_logs}, log_dir={log_dir}")


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger instance with optional context

    Args:
        name: Logger name (usually __name__)
        context: Optional context dictionary to include in all log messages

    Returns:
        Logger or LoggerAdapter instance
    """
    logger = logging.getLogger(name)

    if context:
        return LoggerAdapter(logger, context)

    return logger
