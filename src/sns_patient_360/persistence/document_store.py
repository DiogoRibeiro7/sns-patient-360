"""Document-store contracts and MongoDB implementation for versioned FHIR resources."""

from __future__ import annotations

from typing import Any, Protocol

from pymongo.collection import Collection

from sns_patient_360.ingestion.models import CanonicalClinicalResource


class ClinicalDocumentStore(Protocol):
    """Storage contract for immutable/versioned canonical clinical documents."""

    def upsert_version(self, resource: CanonicalClinicalResource) -> bool:
        """Persist one source resource version.

        Returns ``True`` when a new document is inserted and ``False`` for an exact replay.
        Raises ``ValueError`` when the same source-version key is presented with a different
        payload.
        """

    def list_patient_resources(self, canonical_patient_id: str) -> tuple[dict[str, Any], ...]:
        """Return all stored resource versions for a canonical patient."""


class MongoClinicalDocumentStore:
    """MongoDB-backed store for complete versioned FHIR resource documents."""

    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._collection = collection
        self._collection.create_index(
            [
                ("source_system", 1),
                ("resource_type", 1),
                ("resource_id", 1),
                ("version_id", 1),
            ],
            unique=True,
            name="source_resource_version",
        )
        self._collection.create_index(
            [("canonical_patient_id", 1)],
            name="canonical_patient",
        )

    @staticmethod
    def _key(resource: CanonicalClinicalResource) -> dict[str, str]:
        return {
            "source_system": resource.source_system,
            "resource_type": resource.resource_type,
            "resource_id": resource.resource_id,
            "version_id": resource.version_id,
        }

    def upsert_version(self, resource: CanonicalClinicalResource) -> bool:
        """Insert one immutable source version or recognise an exact replay."""
        key = self._key(resource)
        existing = self._collection.find_one(key)
        if existing is not None:
            if existing.get("payload") != resource.payload:
                raise ValueError(
                    "conflicting payload for an existing source resource version; refusing overwrite"
                )
            return False

        document: dict[str, Any] = {
            **key,
            "canonical_patient_id": resource.canonical_patient_id,
            "payload": resource.payload,
            "provenance": resource.provenance.model_dump(mode="json"),
        }
        self._collection.insert_one(document)
        return True

    def list_patient_resources(self, canonical_patient_id: str) -> tuple[dict[str, Any], ...]:
        """Return complete stored FHIR documents for one canonical patient."""
        documents = self._collection.find(
            {"canonical_patient_id": canonical_patient_id},
            {"_id": 0},
        ).sort(
            [
                ("source_system", 1),
                ("resource_type", 1),
                ("resource_id", 1),
                ("version_id", 1),
            ]
        )
        return tuple(dict(document) for document in documents)
