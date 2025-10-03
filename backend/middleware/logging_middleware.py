"""
Request/Response logging middleware
"""

import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all incoming requests and outgoing responses
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID
        request_id = request.headers.get('X-Request-ID', f"{time.time()}")

        # Log request
        start_time = time.time()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_host': request.client.host if request.client else None,
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_seconds': round(duration, 3),
            }
        )

        # Add custom headers
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Response-Time'] = f"{duration:.3f}s"

        return response


async def logging_middleware(request: Request, call_next: Callable):
    """
    Function-based logging middleware
    """
    middleware = LoggingMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
