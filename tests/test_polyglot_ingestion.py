"""Integration contract for relational identity plus NoSQL clinical documents."""

from __future__ import annotations

from typing import Any

from sns_patient_360.ingestion import CanonicalClinicalStore, IngestionService
from sns_patient_360.ingestion.models import CanonicalClinicalResource
from sns_patient_360.synthetic import generate_journey, source_bundle_to_fhir


class _DocumentStore:
    def __init__(self) -> None:
        self.resources: list[CanonicalClinicalResource] = []

    def upsert_version(self, resource: CanonicalClinicalResource) -> bool:
        key = (
            resource.source_system,
            resource.resource_type,
            resource.resource_id,
            resource.version_id,
        )
        for existing in self.resources:
            existing_key = (
                existing.source_system,
                existing.resource_type,
                existing.resource_id,
                existing.version_id,
            )
            if existing_key != key:
                continue
            if existing.payload != resource.payload:
                raise ValueError("conflicting payload for an existing source resource version")
            return False
        self.resources.append(resource)
        return True

    def list_patient_resources(self, canonical_patient_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(
            resource.model_dump(mode="json")
            for resource in self.resources
            if resource.canonical_patient_id == canonical_patient_id
        )


class _FailOnceDocumentStore(_DocumentStore):
    def __init__(self, fail_after: int) -> None:
        super().__init__()
        self._fail_after = fail_after
        self._calls = 0
        self._failed = False

    def upsert_version(self, resource: CanonicalClinicalResource) -> bool:
        self._calls += 1
        if not self._failed and self._calls > self._fail_after:
            self._failed = True
            raise RuntimeError("simulated MongoDB outage")
        return super().upsert_version(resource)


def test_ingestion_writes_relational_identity_and_document_resources() -> None:
    """Polyglot ingestion keeps identity relational while persisting FHIR documents separately."""
    relational = CanonicalClinicalStore()
    documents = _DocumentStore()
    service = IngestionService(relational, documents)

    results = [
        service.ingest_bundle(source_bundle_to_fhir(bundle))
        for bundle in generate_journey().sources
    ]

    canonical_ids = {result.canonical_patient_id for result in results}
    assert len(canonical_ids) == 1
    assert relational.patient_count() == 1
    assert len(documents.resources) == 17
    assert {resource.source_system for resource in documents.resources} == {
        "primary-care",
        "hospital",
        "laboratory",
        "pharmacy",
    }


def test_replay_repairs_document_store_after_partial_failure() -> None:
    """P1 regression: SQL duplicates must still be offered to MongoDB during replay."""
    relational = CanonicalClinicalStore()
    documents = _FailOnceDocumentStore(fail_after=2)
    service = IngestionService(relational, documents)
    source = generate_journey().sources[0]
    bundle = source_bundle_to_fhir(source)

    first = service.ingest_bundle(bundle)

    assert first.rejected == 1
    assert relational.patient_count() == 1
    assert relational.resource_count() == len(bundle["entry"])
    assert len(documents.resources) == 2
    assert relational.ingestion_event_count("partial") == 1

    replay = service.ingest_bundle(bundle)

    assert replay.rejected == 0
    assert replay.accepted == 0
    assert replay.duplicates == len(bundle["entry"])
    assert relational.resource_count() == len(bundle["entry"])
    assert len(documents.resources) == len(bundle["entry"])
    assert relational.ingestion_event_count("accepted") == 1
