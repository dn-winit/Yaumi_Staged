"""
Global exception handling middleware
"""

import traceback
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.exceptions.base import BaseAPIException
from backend.logging_config import get_logger

logger = get_logger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware
    Catches all exceptions and returns appropriate JSON responses
    """

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response

        except BaseAPIException as exc:
            # Handle custom API exceptions
            logger.warning(
                f"API Exception: {exc.error_code}",
                extra={
                    'error_code': exc.error_code,
                    'message': exc.message,
                    'status_code': exc.status_code,
                    'path': request.url.path,
                    'method': request.method,
                }
            )

            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )

        except ValueError as exc:
            # Handle value errors as validation errors
            logger.warning(
                f"ValueError: {str(exc)}",
                extra={
                    'path': request.url.path,
                    'method': request.method,
                }
            )

            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    'error': 'VALIDATION_ERROR',
                    'message': str(exc),
                    'status_code': 422,
                }
            )

        except Exception as exc:
            # Handle unexpected exceptions
            logger.error(
                f"Unexpected error: {str(exc)}",
                extra={
                    'path': request.url.path,
                    'method': request.method,
                    'traceback': traceback.format_exc(),
                },
                exc_info=True
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected error occurred',
                    'status_code': 500,
                }
            )


async def exception_handler_middleware(request: Request, call_next: Callable):
    """
    Function-based exception handler middleware
    """
    middleware = ExceptionHandlerMiddleware(app=None)
    return await middleware.dispatch(request, call_next)
