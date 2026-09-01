"""Contract tests for the disposable Redis Patient 360 projection cache."""

from __future__ import annotations

from typing import Any, cast

from sns_patient_360.persistence.cache import RedisPatientProjectionCache


class _Redis:
    def __init__(self, value: object = None) -> None:
        self.value = value
        self.deleted: list[str] = []
        self.values: dict[str, str] = {}

    def get(self, key: str) -> object:
        if key in self.values:
            return self.values[key]
        return self.value

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        del ttl_seconds
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)


def _cache(value: object = None) -> tuple[RedisPatientProjectionCache, _Redis]:
    client = _Redis(value)
    return RedisPatientProjectionCache(cast(Any, client)), client


def test_missing_projection_is_cache_miss() -> None:
    cache, _ = _cache()

    assert cache.get("patient:1") is None


def test_valid_projection_is_returned() -> None:
    cache, _ = _cache(b'{"patient_id":"1"}')

    assert cache.get("patient:1") == {"patient_id": "1"}


def test_malformed_json_is_invalidated_and_treated_as_miss() -> None:
    cache, client = _cache(b"not-json")

    assert cache.get("patient:1") is None
    assert client.deleted == ["patient:1"]


def test_non_object_json_is_invalidated_and_treated_as_miss() -> None:
    cache, client = _cache(b"[1,2,3]")

    assert cache.get("patient:1") is None
    assert client.deleted == ["patient:1"]
