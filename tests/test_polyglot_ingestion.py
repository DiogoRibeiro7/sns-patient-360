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
