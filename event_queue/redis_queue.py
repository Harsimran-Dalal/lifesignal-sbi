"""Redis-backed event queue for life-signal processing."""

from __future__ import annotations

import json
from typing import Any

import redis

from config import settings

QUEUE_KEY = "lifesignal:events"


def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_event(customer_id: int, detected_event: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    client = get_redis_client()
    payload = {
        "customer_id": customer_id,
        "detected_event": detected_event,
        "metadata": metadata or {},
    }
    client.lpush(QUEUE_KEY, json.dumps(payload))
    return payload


def dequeue_event(timeout: int = 1) -> dict[str, Any] | None:
    client = get_redis_client()
    result = client.brpop(QUEUE_KEY, timeout=timeout)
    if not result:
        return None
    _, raw = result
    return json.loads(raw)


def queue_length() -> int:
    return get_redis_client().llen(QUEUE_KEY)
