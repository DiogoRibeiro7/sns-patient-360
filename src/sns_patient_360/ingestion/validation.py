"""Minimal validation for the supported synthetic FHIR ingestion boundary."""

from __future__ import annotations

from typing import Any

from sns_patient_360.synthetic.export import (
    SOURCE_URI_PREFIX,
    SYNTHETIC_IDENTIFIER_SYSTEM,
    SYNTHETIC_TAG_SYSTEM,
)

SUPPORTED_RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        "Patient",
        "Encounter",
        "Condition",
        "Observation",
        "DiagnosticReport",
        "ImagingStudy",
        "Endpoint",
        "MedicationRequest",
        "MedicationDispense",
        "AllergyIntolerance",
        "Immunization",
        "Procedure",
        "CarePlan",
        "Appointment",
        "ServiceRequest",
        "DocumentReference",
        "Consent",
        "Provenance",
        "AuditEvent",
    }
)

# Endpoint describes a service connection and is referenced by patient-scoped resources;
# it is not itself required to carry Patient.subject.
SUBJECT_EXEMPT_RESOURCE_TYPES: frozenset[str] = frozenset({"Endpoint"})


class FHIRValidationError(ValueError):
    """Raised when a bundle fails the repository's supported FHIR boundary."""


def _resource_entries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    entries = bundle.get("entry")
    if not isinstance(entries, list) or not entries:
        raise FHIRValidationError("Bundle.entry must be a non-empty list")
    return entries


def validate_bundle(bundle: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    """Validate one source bundle and return source, local patient id and resources."""
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "collection":
        raise FHIRValidationError("Expected a FHIR collection Bundle")

    resources: list[dict[str, Any]] = []
    source_system: str | None = None
    patient_id: str | None = None

    for entry in _resource_entries(bundle):
        resource = entry.get("resource")
        if not isinstance(resource, dict):
            raise FHIRValidationError("Each Bundle.entry must contain a resource object")

        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not isinstance(resource_type, str) or resource_type not in SUPPORTED_RESOURCE_TYPES:
            raise FHIRValidationError(f"Unsupported resource type: {resource_type!r}")
        if not isinstance(resource_id, str) or not resource_id:
            raise FHIRValidationError("Every resource requires a non-empty id")

        meta = resource.get("meta")
        if not isinstance(meta, dict):
            raise FHIRValidationError(f"{resource_type}/{resource_id} requires meta")
        source_uri = meta.get("source")
        if not isinstance(source_uri, str) or not source_uri.startswith(SOURCE_URI_PREFIX):
            raise FHIRValidationError(f"{resource_type}/{resource_id} has invalid meta.source")
        current_source = source_uri.removeprefix(SOURCE_URI_PREFIX)
        if source_system is None:
            source_system = current_source
        elif current_source != source_system:
            raise FHIRValidationError("A source bundle cannot mix source systems")

        tags = meta.get("tag")
        if not isinstance(tags, list) or not any(
            isinstance(tag, dict)
            and tag.get("system") == SYNTHETIC_TAG_SYSTEM
            and tag.get("code") == "synthetic"
            for tag in tags
        ):
            raise FHIRValidationError(f"{resource_type}/{resource_id} is not marked synthetic")

        if resource_type == "Patient":
            if patient_id is not None:
                raise FHIRValidationError("A source bundle must contain exactly one Patient")
            patient_id = resource_id
        resources.append(resource)

    if source_system is None or patient_id is None:
        raise FHIRValidationError("Bundle requires one source system and one Patient")

    for resource in resources:
        resource_type = str(resource["resourceType"])
        if resource_type == "Patient" or resource_type in SUBJECT_EXEMPT_RESOURCE_TYPES:
            continue
        subject = resource.get("subject")
        if not isinstance(subject, dict) or subject.get("reference") != f"Patient/{patient_id}":
            raise FHIRValidationError(
                f"{resource_type}/{resource['id']} must reference Patient/{patient_id}"
            )

    return source_system, patient_id, resources


def extract_synthetic_identifier(patient_resource: dict[str, Any]) -> str:
    """Extract the shared synthetic national identifier used for deterministic matching."""
    identifiers = patient_resource.get("identifier")
    if not isinstance(identifiers, list):
        raise FHIRValidationError("Patient.identifier must be a list")

    matches = [
        item.get("value")
        for item in identifiers
        if isinstance(item, dict) and item.get("system") == SYNTHETIC_IDENTIFIER_SYSTEM
    ]
    if len(matches) != 1 or not isinstance(matches[0], str) or not matches[0]:
        raise FHIRValidationError("Patient must contain exactly one synthetic shared identifier")
    return matches[0]
