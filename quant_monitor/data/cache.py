"""diskcache wrapper with TTL-aware caching.

Uses SQLite-backed diskcache — no Redis needed.
TTL values loaded from config.toml [cache_ttl] section.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from diskcache import Cache

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"


class DataCache:
    """TTL-aware cache backed by diskcache (SQLite)."""

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        """Initialize cache.

        Args:
            cache_dir: Directory for cache files
        """
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(self._cache_dir))
        self._hits = 0
        self._misses = 0
        logger.info(f"Cache initialized at {self._cache_dir}")

    def get(self, key: str) -> Any | None:
        """Get cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        value = self._cache.get(key)
        if value is not None:
            self._hits += 1
            logger.debug(f"Cache HIT: {key}")
        else:
            self._misses += 1
            logger.debug(f"Cache MISS: {key}")
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with TTL in seconds.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)
        """
        if ttl is not None:
            self._cache.set(key, value, expire=ttl)
        else:
            self._cache.set(key, value)
        logger.debug(f"Cache SET: {key} (ttl={ttl})")

    def delete(self, key: str) -> bool:
        """Delete a cached value.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        return self._cache.delete(key)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Return cache hit/miss statistics.

        Returns:
            Dict with hits, misses, hit_rate, size
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "size_bytes": self._cache.volume(),
            "cache_dir": str(self._cache_dir),
        }

    def close(self) -> None:
        """Close the cache."""
        self._cache.close()

    def __enter__(self) -> DataCache:
        return self

    def __exit__(self, *args) -> None:
        self.close()


# Singleton cache instance
_cache: DataCache | None = None


def get_cache() -> DataCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache
