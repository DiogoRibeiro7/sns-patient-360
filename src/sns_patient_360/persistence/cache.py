"""Non-authoritative cache contracts for future Patient 360 projections."""

from __future__ import annotations

import json
from typing import Any, Protocol

from redis import Redis


class PatientProjectionCache(Protocol):
    """Disposable cache contract for derived Patient 360 projections."""

    def get(self, key: str) -> dict[str, Any] | None:
        """Return one cached projection when present."""

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        """Cache one derived projection for a bounded period."""

    def delete(self, key: str) -> None:
        """Invalidate one projection."""


class RedisPatientProjectionCache:
    """Redis-backed cache that never acts as the clinical source of truth."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, key: str) -> dict[str, Any] | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        value = json.loads(str(raw))
        if not isinstance(value, dict):
            raise ValueError("cached patient projection must be a JSON object")
        return value

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._client.setex(key, ttl_seconds, json.dumps(value, sort_keys=True))

    def delete(self, key: str) -> None:
        self._client.delete(key)
