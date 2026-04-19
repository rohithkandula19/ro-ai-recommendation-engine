import asyncio
from loguru import logger
import redis.asyncio as aioredis

from core.config import settings
from tasks.celery_app import celery_app


async def _refresh_inner() -> int:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    keys = []
    async for key in client.scan_iter(match="rec:*:home:*", count=100):
        keys.append(key)
    if keys:
        await client.delete(*keys)
    await client.close()
    return len(keys)


@celery_app.task(name="tasks.cache_refresh_task.refresh_top_users")
def refresh_top_users() -> dict:
    count = asyncio.run(_refresh_inner())
    logger.info(f"Refreshed {count} recommendation cache keys")
    return {"invalidated": count}
