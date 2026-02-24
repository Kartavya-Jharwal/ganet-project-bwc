"""Rate limiter utility for API calls.

Implements a token bucket algorithm to enforce rate limits across different
data sources. Thread-safe for concurrent access.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """Configuration for a rate limiter."""

    requests_per_minute: int
    burst_size: int | None = None  # None = same as requests_per_minute

    def __post_init__(self) -> None:
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute


# Default rate limits for each service
RATE_LIMITS = {
    "yfinance": RateLimitConfig(requests_per_minute=30, burst_size=5),
    "fred": RateLimitConfig(requests_per_minute=120, burst_size=20),
    "sec_edgar": RateLimitConfig(requests_per_minute=10, burst_size=2),
    "google_rss": RateLimitConfig(requests_per_minute=20, burst_size=5),
    "appwrite": RateLimitConfig(requests_per_minute=100, burst_size=20),
    "telegram": RateLimitConfig(requests_per_minute=30, burst_size=10),
}


@dataclass
class TokenBucket:
    """Token bucket rate limiter."""

    config: RateLimitConfig
    tokens: float = field(init=False)
    last_update: float = field(init=False)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.config.burst_size or self.config.requests_per_minute)
        self.last_update = time.monotonic()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        refill_rate = self.config.requests_per_minute / 60.0
        self.tokens = min(
            self.config.burst_size or self.config.requests_per_minute,
            self.tokens + elapsed * refill_rate,
        )
        self.last_update = now

    def acquire(self, timeout: float | None = None) -> bool:
        """Acquire a token, blocking if necessary.

        Args:
            timeout: Max seconds to wait. None = wait forever.

        Returns:
            True if token acquired, False if timeout.
        """
        start = time.monotonic()

        while True:
            with self.lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    return False

            # Wait a bit before retrying
            time.sleep(0.1)

    def try_acquire(self) -> bool:
        """Try to acquire a token without blocking.

        Returns:
            True if token acquired, False otherwise.
        """
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    @property
    def available_tokens(self) -> float:
        """Get current available tokens (approximate)."""
        with self.lock:
            self._refill()
            return self.tokens


class RateLimiter:
    """Manages rate limiters for multiple services."""

    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def get_bucket(self, service: str) -> TokenBucket:
        """Get or create a token bucket for a service."""
        with self._lock:
            if service not in self._buckets:
                config = RATE_LIMITS.get(
                    service,
                    RateLimitConfig(requests_per_minute=60, burst_size=10),
                )
                self._buckets[service] = TokenBucket(config=config)
            return self._buckets[service]

    def wait(self, service: str, timeout: float | None = None) -> bool:
        """Wait for rate limit on a service.

        Args:
            service: Service name (e.g., 'yfinance', 'fred')
            timeout: Max seconds to wait

        Returns:
            True if acquired, False if timeout
        """
        return self.get_bucket(service).acquire(timeout)

    def try_acquire(self, service: str) -> bool:
        """Try to acquire without blocking."""
        return self.get_bucket(service).try_acquire()

    def rate_limited(
        self, service: str, timeout: float | None = 30.0
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to rate limit a function.

        Usage:
            @rate_limiter.rate_limited("yfinance")
            def fetch_price(ticker):
                ...
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                if not self.wait(service, timeout):
                    raise TimeoutError(f"Rate limit timeout for {service}")
                return func(*args, **kwargs)

            return wrapper

        return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()
