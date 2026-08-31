"""Typed models for deterministic synthetic clinical source data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

SourceName = Literal["primary-care", "hospital", "laboratory", "pharmacy"]


class SyntheticPatientIdentity(BaseModel):
    """Shared synthetic identity used to correlate independent source records."""

    model_config = ConfigDict(frozen=True)

    synthetic_master_id: str
    given_name: str
    family_name: str
    birth_date: date
    sex: Literal["male", "female", "other", "unknown"]
    synthetic_national_health_id: str


class SourcePatientIdentity(BaseModel):
    """Source-local representation of one synthetic patient."""

    model_config = ConfigDict(frozen=True)

    source: SourceName
    source_patient_id: str
    synthetic_master_id: str
    synthetic_national_health_id: str


class SyntheticClinicalResource(BaseModel):
    """Minimal FHIR-shaped synthetic resource with explicit source metadata."""

    model_config = ConfigDict(frozen=True)

    source: SourceName
    source_patient_id: str
    resource_type: str
    resource_id: str
    occurred_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyntheticSourceBundle(BaseModel):
    """Independent export for one synthetic source system."""

    model_config = ConfigDict(frozen=True)

    source: SourceName
    generated_at: datetime
    patient: SourcePatientIdentity
    resources: tuple[SyntheticClinicalResource, ...]


class SyntheticJourney(BaseModel):
    """Complete deterministic journey across all simulated source systems."""

    model_config = ConfigDict(frozen=True)

    seed: int
    patient: SyntheticPatientIdentity
    sources: tuple[SyntheticSourceBundle, ...]
