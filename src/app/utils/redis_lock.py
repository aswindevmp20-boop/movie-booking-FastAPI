import time
import uuid
import asyncio
from typing import Optional
import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Acquire a lock key. Returns lock token (unique) if acquired, else None.
async def acquire_lock(key: str, ttl: int = 30, retry_delay: float = 0.05, timeout: float = 3.0) -> Optional[str]:
    token = str(uuid.uuid4())
    end = time.time() + timeout
    while time.time() < end:
        ok = await redis_client.set(key, token, nx=True, ex=ttl)
        if ok:
            return token
        await asyncio.sleep(retry_delay)
    return None

# Release a lock only if token matches
async def release_lock(key: str, token: str) -> bool:
    # Lua script ensures atomic check+del
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    try:
        res = await redis_client.eval(script, 1, key, token)
        return bool(res)
    except Exception:
        return False
