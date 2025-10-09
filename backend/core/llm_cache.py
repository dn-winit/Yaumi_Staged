"""
LLM Response Cache and Rate Limiter
Handles caching of LLM responses and rate limiting to prevent API abuse
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
import threading
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class LLMCache:
    """
    File-based cache for LLM responses with automatic expiration
    Thread-safe, efficient, and production-ready
    """

    def __init__(self, cache_dir: str = None, default_ttl_hours: int = 24):
        """
        Initialize LLM cache

        Args:
            cache_dir: Directory to store cache files (default: backend/cache/llm)
            default_ttl_hours: Default time-to-live for cache entries in hours
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / 'cache' / 'llm'

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self._lock = threading.Lock()

        # Stats
        self.hits = 0
        self.misses = 0
        self.total_cost_saved = 0.0  # Estimated in USD

        logger.info(f"LLM Cache initialized: {self.cache_dir}, TTL={default_ttl_hours}h")

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate unique cache key from parameters"""
        # Sort kwargs for consistent hashing
        sorted_params = sorted(kwargs.items())
        param_string = json.dumps(sorted_params, sort_keys=True)
        hash_digest = hashlib.sha256(param_string.encode()).hexdigest()[:16]
        return f"{prefix}_{hash_digest}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, prefix: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached response if exists and not expired

        Args:
            prefix: Cache key prefix (e.g., 'customer_analysis', 'route_analysis')
            **kwargs: Parameters that uniquely identify this request

        Returns:
            Cached response dict or None if not found/expired
        """
        cache_key = self._generate_cache_key(prefix, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self.misses += 1
            return None

        try:
            with self._lock:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            # Check expiration
            expires_at = datetime.fromisoformat(cache_data['expires_at'])
            if datetime.now() >= expires_at:
                # Expired - delete file
                cache_path.unlink(missing_ok=True)
                self.misses += 1
                logger.debug(f"Cache expired: {cache_key}")
                return None

            # Valid cache hit
            self.hits += 1
            self.total_cost_saved += cache_data.get('estimated_cost', 0.001)

            logger.info(f"Cache HIT: {prefix} (saved ${cache_data.get('estimated_cost', 0.001):.4f})")
            return cache_data['response']

        except Exception as e:
            logger.warning(f"Cache read error for {cache_key}: {e}")
            self.misses += 1
            return None

    def set(
        self,
        prefix: str,
        response: Dict[str, Any],
        ttl_hours: Optional[int] = None,
        estimated_cost: float = 0.001,
        **kwargs
    ):
        """
        Store response in cache

        Args:
            prefix: Cache key prefix
            response: Response data to cache
            ttl_hours: Custom TTL in hours (overrides default)
            estimated_cost: Estimated API cost in USD
            **kwargs: Parameters that uniquely identify this request
        """
        cache_key = self._generate_cache_key(prefix, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        expires_at = datetime.now() + ttl

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'estimated_cost': estimated_cost,
            'response': response
        }

        try:
            with self._lock:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)

            logger.info(f"Cache SET: {prefix} (expires {expires_at.strftime('%Y-%m-%d %H:%M')})")

        except Exception as e:
            logger.error(f"Cache write error for {cache_key}: {e}")

    def clear_expired(self):
        """Remove all expired cache entries"""
        try:
            now = datetime.now()
            removed = 0

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    if now >= expires_at:
                        cache_file.unlink()
                        removed += 1

                except Exception:
                    continue

            if removed > 0:
                logger.info(f"Cleared {removed} expired cache entries")

        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")

    def clear_all(self):
        """Clear entire cache"""
        try:
            removed = 0
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                removed += 1

            logger.info(f"Cleared all cache ({removed} entries)")
            self.hits = 0
            self.misses = 0
            self.total_cost_saved = 0.0

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'total_cost_saved_usd': round(self.total_cost_saved, 4),
            'cache_entries': len(list(self.cache_dir.glob("*.json")))
        }


class RateLimiter:
    """
    Token bucket rate limiter for API calls
    Thread-safe and efficient
    """

    def __init__(self, max_requests: int = 10, time_window_seconds: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in time window
            time_window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window_seconds
        self._tokens = max_requests
        self._last_update = time.time()
        self._lock = threading.Lock()

        logger.info(f"Rate limiter initialized: {max_requests} requests per {time_window_seconds}s")

    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_update

        # Add tokens proportional to elapsed time
        tokens_to_add = (elapsed / self.time_window) * self.max_requests
        self._tokens = min(self.max_requests, self._tokens + tokens_to_add)
        self._last_update = now

    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        """
        Acquire a token to make a request

        Args:
            blocking: If True, wait until token available
            timeout: Maximum time to wait in seconds (only if blocking=True)

        Returns:
            True if token acquired, False if rate limited
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._refill_tokens()

                if self._tokens >= 1:
                    self._tokens -= 1
                    return True

            # Rate limited
            if not blocking:
                logger.warning("Rate limit exceeded (non-blocking)")
                return False

            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                logger.warning(f"Rate limit timeout after {timeout}s")
                return False

            # Wait a bit before retrying
            time.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self._lock:
            self._refill_tokens()
            return {
                'max_requests': self.max_requests,
                'time_window_seconds': self.time_window,
                'available_tokens': round(self._tokens, 2),
                'rate_limit_active': self._tokens < 1
            }


def cached_llm_call(
    cache: LLMCache,
    rate_limiter: RateLimiter,
    cache_prefix: str,
    ttl_hours: int = 24,
    estimated_cost: float = 0.001
):
    """
    Decorator for LLM functions to add caching and rate limiting

    Usage:
        @cached_llm_call(cache, rate_limiter, 'customer_analysis', ttl_hours=24)
        def analyze_customer(...):
            # Your LLM call here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try cache first
            cached_response = cache.get(cache_prefix, **kwargs)
            if cached_response is not None:
                return cached_response

            # Cache miss - need to make API call
            # Check rate limit
            if not rate_limiter.acquire(blocking=True, timeout=5):
                logger.error(f"Rate limit exceeded for {cache_prefix}")
                raise Exception("API rate limit exceeded. Please try again in a moment.")

            # Make actual API call
            try:
                response = func(*args, **kwargs)

                # Cache the response
                cache.set(
                    cache_prefix,
                    response,
                    ttl_hours=ttl_hours,
                    estimated_cost=estimated_cost,
                    **kwargs
                )

                return response

            except Exception as e:
                logger.error(f"LLM call failed for {cache_prefix}: {e}")
                raise

        return wrapper
    return decorator


# Global instances
_llm_cache = None
_rate_limiter = None


def get_llm_cache() -> LLMCache:
    """Get global LLM cache instance with configuration from environment"""
    global _llm_cache
    if _llm_cache is None:
        import os
        from backend.constants.config_constants import DEFAULT_LLM_CACHE_TTL_HOURS

        ttl_hours = int(os.getenv('LLM_CACHE_TTL_HOURS', DEFAULT_LLM_CACHE_TTL_HOURS))
        _llm_cache = LLMCache(default_ttl_hours=ttl_hours)

    return _llm_cache


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance with configuration from environment"""
    global _rate_limiter
    if _rate_limiter is None:
        import os
        from backend.constants.config_constants import (
            DEFAULT_LLM_RATE_LIMIT_MAX_REQUESTS,
            DEFAULT_LLM_RATE_LIMIT_TIME_WINDOW
        )

        max_requests = int(os.getenv('LLM_RATE_LIMIT_MAX_REQUESTS', DEFAULT_LLM_RATE_LIMIT_MAX_REQUESTS))
        time_window = int(os.getenv('LLM_RATE_LIMIT_TIME_WINDOW_SECONDS', DEFAULT_LLM_RATE_LIMIT_TIME_WINDOW))
        _rate_limiter = RateLimiter(max_requests=max_requests, time_window_seconds=time_window)

    return _rate_limiter
