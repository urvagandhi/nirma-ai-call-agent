"""
Resilient Redis Client & Distributed Concurrency Module.

This module provides an enterprise-grade async Redis manager tuned specifically
for Upstash Serverless Redis (TLS/TCP) and standard Redis instances.

Design Invariants & Upstash Patterns:
    - Persistent TLS connection pooling with health_check_interval=30 to prevent
      idle socket drops on Upstash cloud infrastructure.
    - Automatic retry on timeout and configurable socket connect/read deadlines.
    - Atomic distributed locking with unique token verification using Lua scripting
      (preventing accidental lock release by concurrent processes).
    - Cache-aside helpers with mandatory explicit TTL expiration.

Dependencies:
    - redis[asyncio] >= 5.0
"""

import json
import logging
import uuid
from typing import Any, Optional, Tuple
import redis.asyncio as aioredis
from redis.asyncio.client import Redis

from backend.config import settings

logger = logging.getLogger(__name__)

# Atomic unlock Lua script: only delete the lock key if the token matches
LUA_RELEASE_LOCK = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
"""


class RedisManager:
    """
    Singleton manager for asynchronous Redis connections and distributed primitives.
    """

    _instance: Optional["RedisManager"] = None
    _client: Optional[Redis] = None

    def __new__(cls) -> "RedisManager":
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    def get_client(self) -> Redis:
        """
        Retrieves or initializes the shared asynchronous Redis client.

        Configures socket timeouts, keepalive, and periodic health checks
        tuned for Upstash cloud latency and serverless connection lifecycles.
        """
        if self._client is None:
            logger.info("Initializing resilient async Redis client connection...")
            self._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
                socket_keepalive=True,
                health_check_interval=30,  # Ping server every 30s to keep TLS pipe warm
                retry_on_timeout=True,
                max_connections=50,
            )
        return self._client

    async def close(self) -> None:
        """Gracefully closes all underlying connection pool sockets."""
        if self._client is not None:
            logger.info("Closing async Redis connection pool...")
            await self._client.aclose()
            self._client = None

    async def acquire_lock(
        self,
        lock_key: str,
        ttl_seconds: int = 15,
        token: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Acquires a distributed lock using SET NX EX pattern.

        Args:
            lock_key: Redis key representing the shared resource.
            ttl_seconds: Expiration safety timeout in seconds.
            token: Optional unique lock token; if None, generates a UUID4.

        Returns:
            Tuple[bool, str]: (acquired, token)
        """
        client = self.get_client()
        lock_token = token or str(uuid.uuid4())
        prefixed_key = f"lock:{lock_key}" if not lock_key.startswith("lock:") else lock_key

        try:
            acquired = await client.set(
                prefixed_key,
                lock_token,
                nx=True,
                ex=ttl_seconds,
            )
            return (bool(acquired), lock_token)
        except Exception as exc:
            logger.warning("Failed to acquire distributed lock '%s': %s", prefixed_key, exc)
            return (False, lock_token)

    async def release_lock(self, lock_key: str, token: str) -> bool:
        """
        Releases a distributed lock atomically using a Lua script.
        Ensures a process only releases its own lock, not another process's lock.

        Args:
            lock_key: Redis key representing the shared resource.
            token: Token that was returned during acquire_lock.

        Returns:
            bool: True if lock was owned and released, False otherwise.
        """
        client = self.get_client()
        prefixed_key = f"lock:{lock_key}" if not lock_key.startswith("lock:") else lock_key

        try:
            result = await client.eval(LUA_RELEASE_LOCK, 1, prefixed_key, token)
            return result == 1
        except Exception as exc:
            logger.warning("Error releasing distributed lock '%s': %s", prefixed_key, exc)
            return False

    async def cache_get_json(self, key: str) -> Optional[Any]:
        """
        Fetches and deserializes a JSON cached object.

        Args:
            key: Redis cache key.

        Returns:
            Parsed object or None if cache miss or parse error.
        """
        client = self.get_client()
        try:
            val = await client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as exc:
            logger.warning("Redis cache read failure for key '%s': %s", key, exc)
            return None

    async def cache_set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Serializes and sets a JSON object with mandatory TTL.

        Args:
            key: Redis cache key.
            value: Serializable Python object.
            ttl_seconds: Cache TTL in seconds (default: 1 hour).

        Returns:
            bool: True if stored successfully.
        """
        client = self.get_client()
        try:
            serialized = json.dumps(value)
            await client.set(key, serialized, ex=ttl_seconds)
            return True
        except Exception as exc:
            logger.warning("Redis cache write failure for key '%s': %s", key, exc)
            return False


# Global singleton instance
redis_manager = RedisManager()
