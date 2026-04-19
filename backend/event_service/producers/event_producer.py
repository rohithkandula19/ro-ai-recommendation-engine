import json
import os
from typing import Any
from confluent_kafka import Producer


def _producer() -> Producer:
    return Producer({
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        "client.id": "event-producer",
        "acks": "1",
        "compression.type": "snappy",
    })


class EventProducer:
    def __init__(self):
        self.producer = _producer()

    def publish(self, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
        self.producer.produce(
            topic,
            key=key.encode() if key else None,
            value=json.dumps(payload, default=str).encode(),
        )
        self.producer.poll(0)

    def flush(self, timeout: float = 5.0) -> None:
        self.producer.flush(timeout)
