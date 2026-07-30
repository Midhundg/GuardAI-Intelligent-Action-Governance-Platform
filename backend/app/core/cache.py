import json
import time
from typing import Any
import redis

from app.config.settings import settings


class EnterpriseCache:
    """Enterprise Caching layer with Redis primary and thread-safe memory fallback."""

    def __init__(self):
        self._redis_client = None
        self._memory_cache = {}
        try:
            self._redis_client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True, socket_timeout=1.0
            )
            self._redis_client.ping()
        except Exception:
            self._redis_client = None

    def get(self, key: str) -> Any | None:
        if self._redis_client:
            try:
                data = self._redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        # Memory fallback
        if key in self._memory_cache:
            val, expires_at = self._memory_cache[key]
            if expires_at is None or expires_at > time.time():
                return val
            else:
                del self._memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if self._redis_client:
            try:
                self._redis_client.setex(key, ttl_seconds, json.dumps(value))
                return
            except Exception:
                pass
        # Memory fallback
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._memory_cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        if self._redis_client:
            try:
                self._redis_client.delete(key)
            except Exception:
                pass
        self._memory_cache.pop(key, None)

    def clear(self) -> None:
        if self._redis_client:
            try:
                self._redis_client.flushdb()
            except Exception:
                pass
        self._memory_cache.clear()


cache = EnterpriseCache()
