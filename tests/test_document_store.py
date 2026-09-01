"""Contract tests for the MongoDB-backed clinical document store."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

from sns_patient_360.ingestion.models import CanonicalClinicalResource, ProvenanceRecord
from sns_patient_360.persistence.document_store import MongoClinicalDocumentStore


class _Cursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def sort(self, _: list[tuple[str, int]]) -> "_Cursor":
        return self

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._documents)


class _Collection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def create_index(self, *args: Any, **kwargs: Any) -> None:
        return None

    def find_one(self, key: dict[str, str]) -> dict[str, Any] | None:
        for document in self.documents:
            if all(document.get(field) == value for field, value in key.items()):
                return document
        return None

    def insert_one(self, document: dict[str, Any]) -> object:
        self.documents.append(dict(document))
        return object()

    def find(
        self,
        query: dict[str, str],
        projection: dict[str, int],
    ) -> _Cursor:
        del projection
        documents = [
            {key: value for key, value in document.items() if key != "_id"}
            for document in self.documents
            if all(document.get(field) == value for field, value in query.items())
        ]
        return _Cursor(documents)


def _resource(*, version: str = "1", value: float = 6.8) -> CanonicalClinicalResource:
    provenance = ProvenanceRecord(
        source_system="laboratory",
        source_patient_id="LAB-123456",
        resource_type="Observation",
        resource_id="lab-hba1c-2",
        version_id=version,
        ingested_at=datetime(2026, 9, 1, 4, 0, tzinfo=UTC),
    )
    return CanonicalClinicalResource(
        canonical_patient_id="patient-1",
        resource_type="Observation",
        resource_id="lab-hba1c-2",
        version_id=version,
        source_system="laboratory",
        payload={"resourceType": "Observation", "id": "lab-hba1c-2", "value": value},
        provenance=provenance,
    )


def _store() -> MongoClinicalDocumentStore:
    collection = cast(Any, _Collection())
    return MongoClinicalDocumentStore(collection)


def test_new_document_version_is_inserted() -> None:
    store = _store()

    assert store.upsert_version(_resource()) is True
    assert len(store.list_patient_resources("patient-1")) == 1


def test_exact_replay_is_idempotent() -> None:
    store = _store()
    resource = _resource()

    assert store.upsert_version(resource) is True
    assert store.upsert_version(resource) is False
    assert len(store.list_patient_resources("patient-1")) == 1


def test_changed_payload_under_same_version_is_rejected() -> None:
    store = _store()
    store.upsert_version(_resource(value=6.8))

    with pytest.raises(ValueError, match="conflicting payload"):
        store.upsert_version(_resource(value=9.9))


def test_new_version_is_preserved_alongside_old_version() -> None:
    store = _store()

    assert store.upsert_version(_resource(version="1", value=6.8)) is True
    assert store.upsert_version(_resource(version="2", value=6.5)) is True

    resources = store.list_patient_resources("patient-1")
    assert {resource["version_id"] for resource in resources} == {"1", "2"}
