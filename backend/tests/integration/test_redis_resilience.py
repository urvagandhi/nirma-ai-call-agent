"""
Integration Tests — Resilient Redis Manager & Distributed Concurrency Primitives.

Tests `backend.database.redis_client.RedisManager`:
- Distributed locking via SET NX EX pattern.
- Atomic lock release via Lua script (anti-lock-theft protection).
- Cache-aside helpers with JSON serialization and explicit TTL.
- Fault tolerance when Redis experiences exceptions.
"""

import json
import pytest
from backend.database.redis_client import RedisManager


@pytest.mark.asyncio
async def test_redis_acquire_and_release_lock_lifecycle(mock_redis):
    """Verifies that an acquired lock can be released atomically with the matching token."""
    lock_key = "campaign:dispatch:101"
    acquired, token = await mock_redis.acquire_lock(lock_key, ttl_seconds=10)

    assert acquired is True
    assert token is not None

    # Second process tries to acquire the exact same lock key
    second_acquired, _ = await mock_redis.acquire_lock(lock_key, ttl_seconds=10)
    assert second_acquired is False

    # First process releases lock with correct token
    released = await mock_redis.release_lock(lock_key, token)
    assert released is True

    # Now the lock can be acquired again
    third_acquired, new_token = await mock_redis.acquire_lock(lock_key, ttl_seconds=10)
    assert third_acquired is True
    assert new_token != token


@pytest.mark.asyncio
async def test_redis_prevent_lock_theft_with_wrong_token(mock_redis):
    """
    Verifies that a process cannot release another process's lock
    if its token does not match (preventing race condition lock deletion).
    """
    lock_key = "webhook:turn:uuid-1234"
    acquired, legit_token = await mock_redis.acquire_lock(lock_key, ttl_seconds=10)
    assert acquired is True

    # Malicious or stale process attempts to release the lock with an invalid token
    rogue_released = await mock_redis.release_lock(lock_key, "rogue-imposter-token")
    assert rogue_released is False

    # The legitimate owner must still hold the lock
    cant_acquire, _ = await mock_redis.acquire_lock(lock_key, ttl_seconds=10)
    assert cant_acquire is False

    # Clean up with legitimate token
    assert await mock_redis.release_lock(lock_key, legit_token) is True


@pytest.mark.asyncio
async def test_redis_cache_set_and_get_json(mock_redis):
    """Verifies cache_set_json serializes complex objects and cache_get_json retrieves them."""
    key = "cache:script:42"
    payload = {
        "id": 42,
        "name": "Fee Reminder",
        "nested": {"status": "active", "max_turns": 10},
        "tags": ["urgent", "hindi"],
    }

    stored = await mock_redis.cache_set_json(key, payload, ttl_seconds=300)
    assert stored is True

    cached = await mock_redis.cache_get_json(key)
    assert cached == payload


@pytest.mark.asyncio
async def test_redis_cache_miss_returns_none(mock_redis):
    """Verifies cache_get_json returns None for nonexistent keys."""
    cached = await mock_redis.cache_get_json("cache:nonexistent:key")
    assert cached is None
