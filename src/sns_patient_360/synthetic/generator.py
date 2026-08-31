"""Deterministic synthetic patient journey spanning four independent source systems."""

from __future__ import annotations

from datetime import UTC, date, datetime
from random import Random
from typing import Callable

from sns_patient_360.synthetic.models import (
    SourceName,
    SourcePatientIdentity,
    SyntheticClinicalResource,
    SyntheticJourney,
    SyntheticPatientIdentity,
    SyntheticSourceBundle,
)

_FIXED_GENERATED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)


def _patient(seed: int) -> SyntheticPatientIdentity:
    """Build a deterministic synthetic identity for a fixed seed."""
    rng = Random(seed)
    suffix = rng.randint(100000, 999999)
    return SyntheticPatientIdentity(
        synthetic_master_id=f"syn-{seed:04d}-{suffix}",
        given_name="Miguel",
        family_name="Silva",
        birth_date=date(1964, 4, 17),
        sex="male",
        synthetic_national_health_id=f"SNS-SYN-{suffix}",
    )


def _source_identity(
    source: SourceName,
    patient: SyntheticPatientIdentity,
) -> SourcePatientIdentity:
    """Create a source-local identity while preserving synthetic correlation keys."""
    prefix = {
        "primary-care": "USF",
        "hospital": "HOSP",
        "laboratory": "LAB",
        "pharmacy": "PHARM",
    }[source]
    return SourcePatientIdentity(
        source=source,
        source_patient_id=f"{prefix}-{patient.synthetic_master_id[-6:]}",
        synthetic_master_id=patient.synthetic_master_id,
        synthetic_national_health_id=patient.synthetic_national_health_id,
    )


def _resource(
    source: SourceName,
    source_patient_id: str,
    resource_type: str,
    resource_id: str,
    occurred_at: datetime,
    payload: dict[str, object],
) -> SyntheticClinicalResource:
    """Construct one immutable FHIR-shaped synthetic resource."""
    return SyntheticClinicalResource(
        source=source,
        source_patient_id=source_patient_id,
        resource_type=resource_type,
        resource_id=resource_id,
        occurred_at=occurred_at,
        payload=payload,
    )


def _primary_care(patient: SyntheticPatientIdentity) -> SyntheticSourceBundle:
    identity = _source_identity("primary-care", patient)
    resources = (
        _resource(
            "primary-care",
            identity.source_patient_id,
            "Patient",
            "pc-patient-1",
            datetime(2026, 1, 5, 9, 0, tzinfo=UTC),
            {"active": True},
        ),
        _resource(
            "primary-care",
            identity.source_patient_id,
            "Encounter",
            "pc-enc-1",
            datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
            {"status": "finished", "class": "ambulatory"},
        ),
        _resource(
            "primary-care",
            identity.source_patient_id,
            "Condition",
            "pc-cond-htn",
            datetime(2026, 2, 11, 10, 15, tzinfo=UTC),
            {"code": "hypertension", "clinicalStatus": "active"},
        ),
        _resource(
            "primary-care",
            identity.source_patient_id,
            "MedicationRequest",
            "pc-med-ramipril",
            datetime(2026, 2, 11, 10, 20, tzinfo=UTC),
            {"medication": "ramipril", "dose": "5 mg", "status": "active"},
        ),
        _resource(
            "primary-care",
            identity.source_patient_id,
            "ServiceRequest",
            "pc-ref-cardio",
            datetime(2026, 6, 2, 9, 30, tzinfo=UTC),
            {"service": "cardiology", "status": "active"},
        ),
    )
    return SyntheticSourceBundle(
        source="primary-care",
        generated_at=_FIXED_GENERATED_AT,
        patient=identity,
        resources=resources,
    )


def _hospital(patient: SyntheticPatientIdentity) -> SyntheticSourceBundle:
    identity = _source_identity("hospital", patient)
    resources = (
        _resource(
            "hospital",
            identity.source_patient_id,
            "Patient",
            "h-patient-1",
            datetime(2026, 5, 4, 14, 0, tzinfo=UTC),
            {"active": True},
        ),
        _resource(
            "hospital",
            identity.source_patient_id,
            "Encounter",
            "h-ed-1",
            datetime(2026, 5, 4, 14, 12, tzinfo=UTC),
            {"status": "finished", "class": "emergency", "reason": "chest pain"},
        ),
        _resource(
            "hospital",
            identity.source_patient_id,
            "Observation",
            "h-trop-1",
            datetime(2026, 5, 4, 14, 55, tzinfo=UTC),
            {
                "code": "troponin",
                "value": 7.0,
                "unit": "ng/L",
                "interpretation": "normal",
            },
        ),
        _resource(
            "hospital",
            identity.source_patient_id,
            "Encounter",
            "h-cardio-1",
            datetime(2026, 7, 18, 11, 0, tzinfo=UTC),
            {"status": "finished", "class": "ambulatory", "service": "cardiology"},
        ),
        _resource(
            "hospital",
            identity.source_patient_id,
            "DiagnosticReport",
            "h-ecg-1",
            datetime(2026, 7, 18, 11, 25, tzinfo=UTC),
            {"code": "ECG", "conclusion": "normal sinus rhythm"},
        ),
    )
    return SyntheticSourceBundle(
        source="hospital",
        generated_at=_FIXED_GENERATED_AT,
        patient=identity,
        resources=resources,
    )


def _laboratory(patient: SyntheticPatientIdentity) -> SyntheticSourceBundle:
    identity = _source_identity("laboratory", patient)
    values = (
        ("lab-hba1c-1", "HbA1c", 7.4, "%", datetime(2026, 3, 3, 8, 10, tzinfo=UTC)),
        ("lab-hba1c-2", "HbA1c", 6.8, "%", datetime(2026, 8, 23, 8, 10, tzinfo=UTC)),
        (
            "lab-creat-1",
            "creatinine",
            0.91,
            "mg/dL",
            datetime(2026, 8, 23, 8, 12, tzinfo=UTC),
        ),
    )
    resources = tuple(
        _resource(
            "laboratory",
            identity.source_patient_id,
            "Observation",
            resource_id,
            occurred_at,
            {"code": code, "value": value, "unit": unit, "status": "final"},
        )
        for resource_id, code, value, unit, occurred_at in values
    )
    return SyntheticSourceBundle(
        source="laboratory",
        generated_at=_FIXED_GENERATED_AT,
        patient=identity,
        resources=resources,
    )


def _pharmacy(patient: SyntheticPatientIdentity) -> SyntheticSourceBundle:
    identity = _source_identity("pharmacy", patient)
    resources = (
        _resource(
            "pharmacy",
            identity.source_patient_id,
            "MedicationRequest",
            "pharm-rx-1",
            datetime(2026, 2, 11, 16, 0, tzinfo=UTC),
            {"medication": "ramipril", "dose": "5 mg", "status": "active"},
        ),
        _resource(
            "pharmacy",
            identity.source_patient_id,
            "MedicationDispense",
            "pharm-disp-1",
            datetime(2026, 2, 12, 17, 20, tzinfo=UTC),
            {"medication": "ramipril", "quantity": 30, "status": "completed"},
        ),
    )
    return SyntheticSourceBundle(
        source="pharmacy",
        generated_at=_FIXED_GENERATED_AT,
        patient=identity,
        resources=resources,
    )


_GENERATORS: tuple[Callable[[SyntheticPatientIdentity], SyntheticSourceBundle], ...] = (
    _primary_care,
    _hospital,
    _laboratory,
    _pharmacy,
)


def generate_journey(seed: int = 360) -> SyntheticJourney:
    """Generate the canonical reproducible cross-source synthetic patient journey."""
    if not isinstance(seed, int):
        raise TypeError("seed must be an int")
    if seed < 0:
        raise ValueError("seed must be non-negative")

    patient = _patient(seed)
    sources = tuple(generator(patient) for generator in _GENERATORS)
    return SyntheticJourney(seed=seed, patient=patient, sources=sources)
