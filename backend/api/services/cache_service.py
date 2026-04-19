import json
from typing import Any
import redis.asyncio as aioredis


class CacheService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        raw = await self.redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self.redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def delete_pattern(self, pattern: str) -> int:
        count = 0
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)
            count += 1
        return count

    async def zadd_trending(self, content_id: str, score: float) -> None:
        await self.redis.zincrby("trending:global", score, content_id)

    async def top_trending(self, limit: int = 100) -> list[tuple[str, float]]:
        results = await self.redis.zrevrange("trending:global", 0, limit - 1, withscores=True)
        return results

    async def mark_seen(self, user_id: str, content_id: str, ttl_days: int = 30) -> None:
        await self.redis.sadd(f"seen:{user_id}", content_id)
        await self.redis.expire(f"seen:{user_id}", ttl_days * 86400)

    async def get_seen(self, user_id: str) -> set[str]:
        members = await self.redis.smembers(f"seen:{user_id}")
        return set(members) if members else set()

    async def store_refresh_token(self, user_id: str, jti: str, ttl_days: int) -> None:
        await self.redis.set(f"refresh:{user_id}:{jti}", "1", ex=ttl_days * 86400)

    async def is_refresh_valid(self, user_id: str, jti: str) -> bool:
        return bool(await self.redis.exists(f"refresh:{user_id}:{jti}"))

    async def revoke_refresh(self, user_id: str, jti: str) -> None:
        await self.redis.delete(f"refresh:{user_id}:{jti}")
