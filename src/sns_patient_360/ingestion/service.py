"""Canonical ingestion service for validated FHIR source bundles."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sns_patient_360.ingestion.models import (
    CanonicalClinicalResource,
    IngestionResult,
    ProvenanceRecord,
)
from sns_patient_360.ingestion.store import CanonicalClinicalStore
from sns_patient_360.ingestion.validation import (
    FHIRValidationError,
    extract_synthetic_identifier,
    validate_bundle,
)
from sns_patient_360.persistence.document_store import ClinicalDocumentStore


class IngestionService:
    """Validate, resolve and persist one source bundle.

    Relational identity/audit state is handled by ``CanonicalClinicalStore``. When a
    ``ClinicalDocumentStore`` is configured, complete versioned FHIR resources are also
    written to the document store using the same deterministic source-version key.

    PostgreSQL/SQLite and the document store do not share one transaction. The service
    therefore offers every canonical resource to the document store on every replay. If
    document persistence fails after the relational transaction commits, the attempt is
    recorded as ``partial`` and a later replay can converge the two stores safely.
    """

    def __init__(
        self,
        store: CanonicalClinicalStore,
        document_store: ClinicalDocumentStore | None = None,
    ) -> None:
        if not isinstance(store, CanonicalClinicalStore):
            raise TypeError("store must be a CanonicalClinicalStore")
        self._store = store
        self._document_store = document_store

    def ingest_bundle(self, bundle: dict[str, Any]) -> IngestionResult:
        """Ingest one source bundle with deterministic identity resolution and provenance."""
        ingested_at = datetime.now(UTC)
        source_hint = self._source_hint(bundle)
        event_key = f"{source_hint}:{ingested_at.isoformat()}:{id(bundle)}"
        event_id = str(uuid5(NAMESPACE_URL, event_key))

        try:
            source_system, source_patient_id, resources = validate_bundle(bundle)
            patient_resource = next(
                resource for resource in resources if resource["resourceType"] == "Patient"
            )
            shared_identifier = extract_synthetic_identifier(patient_resource)
        except (FHIRValidationError, StopIteration) as exc:
            self._store.record_ingestion_event(
                event_id=event_id,
                source_system=source_hint,
                outcome="rejected",
                detail=str(exc),
                occurred_at=ingested_at,
            )
            return IngestionResult(
                source_system=source_hint,
                canonical_patient_id=None,
                accepted=0,
                duplicates=0,
                rejected=1,
                errors=(str(exc),),
            )

        canonical_patient_id = str(
            uuid5(NAMESPACE_URL, f"sns-patient-360:patient:{shared_identifier}")
        )
        accepted = 0
        duplicates = 0
        canonical_documents: list[CanonicalClinicalResource] = []

        try:
            with self._store.transaction() as connection:
                patient = self._store.resolve_patient_by_identifier(connection, shared_identifier)
                if patient is None:
                    patient = self._store.create_patient(
                        connection,
                        canonical_patient_id,
                        shared_identifier,
                    )
                elif patient.canonical_patient_id != canonical_patient_id:
                    raise ValueError("canonical identity does not match deterministic resolution")

                self._store.attach_alias(
                    connection,
                    source_system,
                    source_patient_id,
                    canonical_patient_id,
                )

                for resource in resources:
                    meta = resource["meta"]
                    version_id = str(meta.get("versionId", "1"))
                    canonical = CanonicalClinicalResource(
                        canonical_patient_id=canonical_patient_id,
                        resource_type=str(resource["resourceType"]),
                        resource_id=str(resource["id"]),
                        version_id=version_id,
                        source_system=source_system,
                        payload=resource,
                        provenance=ProvenanceRecord(
                            source_system=source_system,
                            source_patient_id=source_patient_id,
                            resource_type=str(resource["resourceType"]),
                            resource_id=str(resource["id"]),
                            version_id=version_id,
                            ingested_at=ingested_at,
                        ),
                    )
                    canonical_documents.append(canonical)
                    if self._store.resource_exists(connection, canonical):
                        duplicates += 1
                    else:
                        self._store.insert_resource(connection, canonical)
                        accepted += 1
        except ValueError as exc:
            self._store.record_ingestion_event(
                event_id=event_id,
                source_system=source_system,
                outcome="rejected",
                detail=str(exc),
                occurred_at=ingested_at,
            )
            return IngestionResult(
                source_system=source_system,
                canonical_patient_id=canonical_patient_id,
                accepted=0,
                duplicates=0,
                rejected=1,
                errors=(str(exc),),
            )

        if self._document_store is not None:
            try:
                for canonical in canonical_documents:
                    self._document_store.upsert_version(canonical)
            except Exception as exc:
                detail = (
                    "document-store persistence incomplete; safe replay required: "
                    f"{type(exc).__name__}: {exc}"
                )
                self._store.record_ingestion_event(
                    event_id=event_id,
                    source_system=source_system,
                    outcome="partial",
                    detail=detail,
                    occurred_at=ingested_at,
                )
                return IngestionResult(
                    source_system=source_system,
                    canonical_patient_id=canonical_patient_id,
                    accepted=0,
                    duplicates=0,
                    rejected=1,
                    errors=(detail,),
                )

        self._store.record_ingestion_event(
            event_id=event_id,
            source_system=source_system,
            outcome="accepted",
            detail=f"accepted={accepted};duplicates={duplicates}",
            occurred_at=ingested_at,
        )
        return IngestionResult(
            source_system=source_system,
            canonical_patient_id=canonical_patient_id,
            accepted=accepted,
            duplicates=duplicates,
            rejected=0,
        )

    @staticmethod
    def _source_hint(bundle: dict[str, Any]) -> str:
        """Extract a best-effort source label for rejected-bundle audit records."""
        entries = bundle.get("entry")
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                resource = entry.get("resource")
                if not isinstance(resource, dict):
                    continue
                meta = resource.get("meta")
                if isinstance(meta, dict) and isinstance(meta.get("source"), str):
                    return str(meta["source"])
        return "unknown"
