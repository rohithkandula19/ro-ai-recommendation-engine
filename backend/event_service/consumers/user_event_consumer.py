import json
import os
from datetime import datetime, timezone
from typing import Any

import clickhouse_connect
from confluent_kafka import Consumer, KafkaError, Producer
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from schemas.event_schema import Event


EVENTS_TOPIC = "user.events"
DLQ_TOPIC = "user.events.dlq"


class UserEventConsumer:
    def __init__(self):
        self.consumer = Consumer({
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": "user-event-consumer",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.dlq = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")})
        self.engine = create_async_engine(
            os.getenv("DATABASE_URL", "postgresql+asyncpg://recuser:recpass@postgres:5432/recengine"),
            pool_size=5, max_overflow=10,
        )
        try:
            self.ch = clickhouse_connect.get_client(
                host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
                port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            )
            self._ensure_clickhouse_table()
        except Exception as e:
            logger.warning(f"ClickHouse unavailable, skipping: {e}")
            self.ch = None

    def _ensure_clickhouse_table(self):
        if self.ch is None:
            return
        self.ch.command("""
            CREATE TABLE IF NOT EXISTS user_events (
                user_id String,
                content_id Nullable(String),
                event_type String,
                value Nullable(Float64),
                session_id Nullable(String),
                device_type Nullable(String),
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (created_at, user_id)
        """)

    def _send_dlq(self, raw: bytes, error: str):
        try:
            self.dlq.produce(DLQ_TOPIC, value=raw, headers=[("error", error.encode())])
            self.dlq.poll(0)
        except Exception as e:
            logger.error(f"DLQ publish failed: {e}")

    async def _write_pg(self, e: dict[str, Any]):
        if e.get("content_id") is None:
            return
        async with self.engine.begin() as conn:
            await conn.execute(text("""
                INSERT INTO interactions (user_id, content_id, event_type, value, session_id, device_type, created_at)
                VALUES (:user_id, :content_id, :event_type, :value, :session_id, :device_type, :created_at)
            """), {
                "user_id": e["user_id"],
                "content_id": e["content_id"],
                "event_type": e["event_type"],
                "value": e.get("value"),
                "session_id": e.get("session_id"),
                "device_type": e.get("device_type"),
                "created_at": e.get("timestamp") or datetime.now(timezone.utc),
            })

    def _write_ch(self, e: dict[str, Any]):
        if self.ch is None:
            return
        self.ch.insert(
            "user_events",
            [[
                e["user_id"], e.get("content_id"), e["event_type"],
                e.get("value"), e.get("session_id"), e.get("device_type"),
                e.get("timestamp") or datetime.now(timezone.utc),
            ]],
            column_names=[
                "user_id", "content_id", "event_type", "value",
                "session_id", "device_type", "created_at",
            ],
        )

    async def run(self):
        self.consumer.subscribe([EVENTS_TOPIC])
        logger.info(f"Subscribed to {EVENTS_TOPIC}")
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"kafka err: {msg.error()}")
                continue
            raw = msg.value()
            try:
                data = json.loads(raw.decode())
                Event.model_validate(data)
                await self._write_pg(data)
                self._write_ch(data)
                self.consumer.commit(msg)
            except Exception as e:
                logger.error(f"event processing failed: {e}")
                self._send_dlq(raw, str(e))
                self.consumer.commit(msg)
