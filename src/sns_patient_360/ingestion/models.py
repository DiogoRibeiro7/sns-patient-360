"""Typed domain models for canonical clinical ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

IngestionStatus = Literal["accepted", "duplicate", "rejected"]


class CanonicalPatient(BaseModel):
    """Canonical identity assembled from one or more source-local Patient records."""

    model_config = ConfigDict(frozen=True)

    canonical_patient_id: str
    synthetic_national_health_id: str
    source_patient_ids: dict[str, str] = Field(default_factory=dict)


class ProvenanceRecord(BaseModel):
    """Provenance retained for one canonical resource version."""

    model_config = ConfigDict(frozen=True)

    source_system: str
    source_patient_id: str
    resource_type: str
    resource_id: str
    version_id: str
    ingested_at: datetime


class CanonicalClinicalResource(BaseModel):
    """Validated source resource preserved in the canonical longitudinal store."""

    model_config = ConfigDict(frozen=True)

    canonical_patient_id: str
    resource_type: str
    resource_id: str
    version_id: str
    source_system: str
    payload: dict[str, Any]
    provenance: ProvenanceRecord

    @property
    def source_key(self) -> tuple[str, str, str, str]:
        """Return the idempotency key for this resource version."""
        return (
            self.source_system,
            self.resource_type,
            self.resource_id,
            self.version_id,
        )


class IngestionResult(BaseModel):
    """Summary of one source-bundle ingestion operation."""

    model_config = ConfigDict(frozen=True)

    source_system: str
    canonical_patient_id: str | None
    accepted: int
    duplicates: int
    rejected: int
    errors: tuple[str, ...] = ()
