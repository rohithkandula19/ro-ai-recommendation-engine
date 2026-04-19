"""Structured JSON logging via loguru."""
import json
import os
import sys
from loguru import logger


def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO")
    json_logs = os.getenv("JSON_LOGS", "0") == "1"

    logger.remove()
    if json_logs:
        def _json_sink(message):
            rec = message.record
            payload = {
                "ts": rec["time"].isoformat(),
                "level": rec["level"].name,
                "msg": rec["message"],
                "logger": rec["name"],
                "file": f"{rec['file'].name}:{rec['line']}",
                **{k: v for k, v in rec["extra"].items() if k != "request_id"},
            }
            if "request_id" in rec["extra"]:
                payload["request_id"] = rec["extra"]["request_id"]
            sys.stderr.write(json.dumps(payload) + "\n")
            sys.stderr.flush()
        logger.add(_json_sink, level=level)
    else:
        logger.add(sys.stderr, level=level,
                   format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | {extra[request_id]!s:.8s} | {name}:{function}:{line} | {message}")
