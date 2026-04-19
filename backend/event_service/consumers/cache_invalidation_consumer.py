import json
import os

import redis.asyncio as aioredis
from confluent_kafka import Consumer, KafkaError
from loguru import logger


SIGNIFICANT_EVENTS = {"complete", "like", "dislike", "rate"}


class CacheInvalidationConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": "cache-invalidation",
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        })
        self.redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

    async def _invalidate(self, user_id: str):
        pattern = f"rec:{user_id}:*"
        deleted = 0
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)
            deleted += 1
        if deleted:
            logger.info(f"invalidated {deleted} cache keys for user {user_id}")

    async def run(self):
        self.consumer.subscribe(["user.events"])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None or msg.error():
                if msg and msg.error() and msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"cache invalidation err: {msg.error()}")
                continue
            try:
                data = json.loads(msg.value().decode())
                if data.get("event_type") in SIGNIFICANT_EVENTS and data.get("user_id"):
                    await self._invalidate(data["user_id"])
            except Exception as e:
                logger.error(f"cache invalidation processing: {e}")
