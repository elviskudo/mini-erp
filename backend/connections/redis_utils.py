"""
Redis Cache Utilities for Mini-ERP
Provides caching and session management
"""
import os
import json
from typing import Optional, Any
import redis.asyncio as redis
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Global Redis connection pool
_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection with connection pooling."""
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
        logger.info(f"Redis connected to {REDIS_URL}")
    
    return _redis_pool


async def close_redis():
    """Close Redis connection."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("Redis connection closed")


# ========== CACHING FUNCTIONS ==========

async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    try:
        r = await get_redis()
        value = await r.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set a value in cache with TTL (default 1 hour)."""
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    try:
        r = await get_redis()
        await r.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


async def cache_invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching a pattern."""
    try:
        r = await get_redis()
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await r.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.error(f"Cache invalidate pattern error: {e}")
        return 0


# ========== SESSION FUNCTIONS ==========

async def session_set(session_id: str, data: dict, ttl: int = 86400) -> bool:
    """Store session data (default 24 hours)."""
    key = f"session:{session_id}"
    return await cache_set(key, data, ttl)


async def session_get(session_id: str) -> Optional[dict]:
    """Get session data."""
    key = f"session:{session_id}"
    return await cache_get(key)


async def session_delete(session_id: str) -> bool:
    """Delete a session."""
    key = f"session:{session_id}"
    return await cache_delete(key)


async def session_extend(session_id: str, ttl: int = 86400) -> bool:
    """Extend session TTL."""
    try:
        r = await get_redis()
        key = f"session:{session_id}"
        await r.expire(key, ttl)
        return True
    except Exception as e:
        logger.error(f"Session extend error: {e}")
        return False


# ========== RATE LIMITING ==========

async def rate_limit_check(key: str, max_requests: int, window_seconds: int) -> bool:
    """
    Check if rate limit is exceeded.
    Returns True if allowed, False if rate limited.
    """
    try:
        r = await get_redis()
        full_key = f"ratelimit:{key}"
        
        current = await r.incr(full_key)
        
        if current == 1:
            await r.expire(full_key, window_seconds)
        
        return current <= max_requests
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True  # Allow on error


# ========== DISTRIBUTED LOCKS ==========

async def acquire_lock(lock_name: str, ttl: int = 30) -> bool:
    """Acquire a distributed lock."""
    try:
        r = await get_redis()
        key = f"lock:{lock_name}"
        result = await r.set(key, "1", nx=True, ex=ttl)
        return result is True
    except Exception as e:
        logger.error(f"Lock acquire error: {e}")
        return False


async def release_lock(lock_name: str) -> bool:
    """Release a distributed lock."""
    try:
        r = await get_redis()
        key = f"lock:{lock_name}"
        await r.delete(key)
        return True
    except Exception as e:
        logger.error(f"Lock release error: {e}")
        return False


# ========== TENANT-AWARE CACHING ==========

def tenant_key(tenant_id: str, key: str) -> str:
    """Generate a tenant-scoped cache key."""
    return f"tenant:{tenant_id}:{key}"


async def tenant_cache_get(tenant_id: str, key: str) -> Optional[Any]:
    """Get tenant-scoped cache value."""
    return await cache_get(tenant_key(tenant_id, key))


async def tenant_cache_set(tenant_id: str, key: str, value: Any, ttl: int = 3600) -> bool:
    """Set tenant-scoped cache value."""
    return await cache_set(tenant_key(tenant_id, key), value, ttl)


async def tenant_cache_invalidate(tenant_id: str) -> int:
    """Invalidate all cache for a specific tenant."""
    return await cache_invalidate_pattern(f"tenant:{tenant_id}:*")
