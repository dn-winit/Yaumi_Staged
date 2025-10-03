"""
Request validation middleware
"""

from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logging_config import get_logger
from backend.constants.config_constants import MAX_REQUEST_SIZE_MB, REQUEST_TIMEOUT

logger = get_logger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates incoming requests
    """

    def __init__(self, app, max_request_size_bytes: int = MAX_REQUEST_SIZE_MB * 1024 * 1024):
        super().__init__(app)
        self.max_request_size_bytes = max_request_size_bytes

    async def dispatch(self, request: Request, call_next: Callable):
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_request_size_bytes:
                    logger.warning(
                        f"Request too large: {content_length} bytes",
                        extra={
                            'content_length': content_length,
                            'max_allowed': self.max_request_size_bytes,
                            'path': request.url.path,
                        }
                    )
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            'error': 'REQUEST_TOO_LARGE',
                            'message': f'Request size exceeds maximum allowed size of {self.max_request_size_bytes / (1024*1024)}MB',
                            'status_code': 413,
                        }
                    )
            except ValueError:
                pass

        # Process request
        response = await call_next(request)
        return response


async def request_validation_middleware(request: Request, call_next: Callable):
    """
    Function-based request validation middleware
    """
    middleware = RequestValidationMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
