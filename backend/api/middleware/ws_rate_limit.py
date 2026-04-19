"""Per-IP in-memory rate limit for WebSocket connects."""
import time
from collections import defaultdict


_connects: dict[str, list[float]] = defaultdict(list)
MAX_PER_MINUTE = 30


def allow_connect(ip: str) -> bool:
    now = time.time()
    window = _connects[ip]
    _connects[ip] = [t for t in window if now - t < 60]
    if len(_connects[ip]) >= MAX_PER_MINUTE:
        return False
    _connects[ip].append(now)
    return True
