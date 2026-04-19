import json
from typing import Any, Optional
from confluent_kafka import Producer
from loguru import logger

from core.config import settings

_producer: Optional[Producer] = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "api-producer",
            "acks": "1",
            "linger.ms": 10,
            "compression.type": "snappy",
        })
    return _producer


def publish(topic: str, payload: dict[str, Any], key: str | None = None) -> None:
    producer = get_producer()
    try:
        producer.produce(
            topic,
            key=key.encode() if key else None,
            value=json.dumps(payload, default=str).encode(),
        )
        producer.poll(0)
    except BufferError:
        producer.flush(timeout=2)
        producer.produce(topic, key=key.encode() if key else None, value=json.dumps(payload, default=str).encode())
    except Exception as e:
        logger.error(f"kafka publish failed topic={topic} err={e}")


def check_kafka_health() -> bool:
    try:
        producer = get_producer()
        md = producer.list_topics(timeout=2)
        return len(md.brokers) > 0
    except Exception:
        return False
