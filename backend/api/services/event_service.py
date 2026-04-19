from core.kafka import publish
from repositories.interaction_repo import InteractionRepo
from services.cache_service import CacheService


class EventService:
    EVENTS_TOPIC = "user.events"
    RETRAIN_TOPIC = "model.retrain.trigger"

    def __init__(self, interaction_repo: InteractionRepo, cache: CacheService):
        self.interaction_repo = interaction_repo
        self.cache = cache

    async def ingest(self, events: list[dict]) -> tuple[int, int]:
        rejected = 0
        valid = []
        for e in events:
            if e.get("user_id") is None or e.get("event_type") is None:
                rejected += 1
                continue
            valid.append(e)

        for ev in valid:
            publish(
                self.EVENTS_TOPIC,
                {
                    "user_id": str(ev["user_id"]),
                    "content_id": str(ev["content_id"]) if ev.get("content_id") else None,
                    "event_type": ev["event_type"],
                    "value": ev.get("value"),
                    "session_id": str(ev["session_id"]) if ev.get("session_id") else None,
                    "device_type": ev.get("device_type"),
                    "timestamp": ev.get("timestamp").isoformat() if ev.get("timestamp") else None,
                },
                key=str(ev["user_id"]),
            )
            if ev.get("content_id") and ev["event_type"] in ("click", "play", "complete"):
                await self.cache.zadd_trending(str(ev["content_id"]), 1.0)

        accepted = await self.interaction_repo.insert_batch(valid)
        return accepted, rejected
