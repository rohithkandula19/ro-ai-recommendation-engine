import json
import os

from confluent_kafka import Consumer, KafkaError, Producer
from loguru import logger


RETRAIN_TOPIC = "model.retrain.trigger"
RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_THRESHOLD", "10000"))


class RetrainTriggerConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": "retrain-trigger",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        })
        self.producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")})
        self.count = 0

    def _fire(self):
        payload = {"reason": "event_count_threshold", "accumulated": self.count}
        self.producer.produce(RETRAIN_TOPIC, value=json.dumps(payload).encode())
        self.producer.poll(0)
        logger.info(f"published retrain trigger after {self.count} events")
        self.count = 0

    async def run(self):
        self.consumer.subscribe(["user.events"])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None or msg.error():
                if msg and msg.error() and msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"retrain trigger err: {msg.error()}")
                continue
            self.count += 1
            if self.count >= RETRAIN_THRESHOLD:
                self._fire()
