import asyncio
from loguru import logger

from consumers.cache_invalidation_consumer import CacheInvalidationConsumer
from consumers.retrain_trigger_consumer import RetrainTriggerConsumer
from consumers.user_event_consumer import UserEventConsumer


async def main():
    user_c = UserEventConsumer()
    cache_c = CacheInvalidationConsumer()
    retrain_c = RetrainTriggerConsumer()

    logger.info("Starting event service consumers")
    await asyncio.gather(
        user_c.run(),
        cache_c.run(),
        retrain_c.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
