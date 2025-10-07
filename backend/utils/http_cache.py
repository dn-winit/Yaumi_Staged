"""
HTTP Caching Utilities
Provides clean, reusable caching headers for API responses
"""

import hashlib
import json
from typing import Any, Dict, Optional
from fastapi import Response
from fastapi.responses import JSONResponse


def generate_etag(data: Any) -> str:
    """
    Generate ETag from response data for cache validation

    Args:
        data: Response data (dict, list, or any JSON-serializable object)

    Returns:
        ETag hash string
    """
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()


def create_cached_response(
    data: Dict[str, Any],
    max_age: int = 3600,
    stale_while_revalidate: Optional[int] = None,
    must_revalidate: bool = False
) -> JSONResponse:
    """
    Create JSON response with appropriate cache headers

    Args:
        data: Response data
        max_age: Cache duration in seconds (default: 1 hour)
        stale_while_revalidate: Allow stale content while revalidating (seconds)
        must_revalidate: Force revalidation after expiry

    Returns:
        JSONResponse with cache headers
    """
    etag = generate_etag(data)

    # Build Cache-Control header
    cache_parts = [f"public, max-age={max_age}"]

    if stale_while_revalidate:
        cache_parts.append(f"stale-while-revalidate={stale_while_revalidate}")

    if must_revalidate:
        cache_parts.append("must-revalidate")

    cache_control = ", ".join(cache_parts)

    return JSONResponse(
        content=data,
        headers={
            "Cache-Control": cache_control,
            "ETag": f'"{etag}"',
            "Vary": "Accept-Encoding"
        }
    )


# Predefined cache configurations for different endpoint types
CACHE_CONFIGS = {
    "filter_options": {
        "max_age": 3600,  # 1 hour - filter options don't change often
        "stale_while_revalidate": 1800,  # Allow 30 min stale while revalidating
    },
    "recommendations": {
        "max_age": 86400,  # 24 hours - recommendations for past dates are static
        "stale_while_revalidate": 3600,  # Allow 1 hour stale
    },
    "dashboard_data": {
        "max_age": 1800,  # 30 minutes - dashboard data updates moderately
        "stale_while_revalidate": 900,  # Allow 15 min stale
    },
    "no_cache": {
        "max_age": 0,  # No caching - always fetch fresh
        "must_revalidate": True
    }
}


def cached_response(
    data: Dict[str, Any],
    cache_type: str = "filter_options"
) -> JSONResponse:
    """
    Convenience function to create cached response with predefined config

    Args:
        data: Response data
        cache_type: Type of cache config to use (from CACHE_CONFIGS)

    Returns:
        JSONResponse with appropriate cache headers
    """
    config = CACHE_CONFIGS.get(cache_type, CACHE_CONFIGS["no_cache"])
    return create_cached_response(data, **config)
