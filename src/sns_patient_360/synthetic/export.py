"""Export deterministic synthetic source bundles as FHIR-shaped JSON documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sns_patient_360.synthetic.models import SyntheticJourney, SyntheticSourceBundle

SYNTHETIC_TAG_SYSTEM = "https://example.invalid/sns-patient-360/synthetic"
SYNTHETIC_IDENTIFIER_SYSTEM = (
    "https://example.invalid/sns-patient-360/synthetic-national-health-id"
)
SOURCE_URI_PREFIX = "urn:sns-patient-360:source:"


def _meta(source: str) -> dict[str, Any]:
    """Build deterministic source and synthetic metadata for one exported resource."""
    return {
        "source": f"{SOURCE_URI_PREFIX}{source}",
        "versionId": "1",
        "tag": [{"system": SYNTHETIC_TAG_SYSTEM, "code": "synthetic"}],
    }


def _patient_resource(bundle: SyntheticSourceBundle) -> dict[str, Any]:
    """Build the source-local Patient resource used for cross-source identity resolution."""
    return {
        "resourceType": "Patient",
        "id": bundle.patient.source_patient_id,
        "active": True,
        "identifier": [
            {
                "system": SYNTHETIC_IDENTIFIER_SYSTEM,
                "value": bundle.patient.synthetic_national_health_id,
            }
        ],
        "name": [
            {
                "use": "official",
                "family": bundle.patient.family_name,
                "given": [bundle.patient.given_name],
            }
        ],
        "birthDate": bundle.patient.birth_date.isoformat(),
        "gender": bundle.patient.sex,
        "meta": _meta(bundle.source),
    }


def source_bundle_to_fhir(bundle: SyntheticSourceBundle) -> dict[str, Any]:
    """Convert one source bundle into a deterministic FHIR Bundle-shaped document.

    Every export contains exactly one source-local ``Patient`` resource. Other resources
    reference that local patient. The shared synthetic national identifier is carried only
    as an explicit Patient identifier so later identity resolution can operate from the
    exported bundle rather than from generator internals.
    """
    entries: list[dict[str, Any]] = [{"resource": _patient_resource(bundle)}]

    for resource in bundle.resources:
        if resource.resource_type == "Patient":
            continue

        fhir_resource: dict[str, Any] = {
            "resourceType": resource.resource_type,
            "id": resource.resource_id,
            "subject": {"reference": f"Patient/{bundle.patient.source_patient_id}"},
            "meta": _meta(bundle.source),
            **resource.payload,
        }
        if resource.occurred_at is not None:
            fhir_resource["effectiveDateTime"] = resource.occurred_at.isoformat()
        entries.append({"resource": fhir_resource})

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": bundle.generated_at.isoformat(),
        "identifier": {
            "system": "https://example.invalid/sns-patient-360/source-bundle",
            "value": f"{bundle.source}-{bundle.patient.source_patient_id}",
        },
        "entry": entries,
    }


def export_journey(journey: SyntheticJourney, output_dir: Path) -> tuple[Path, ...]:
    """Write one independent JSON bundle per source and return created paths."""
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a pathlib.Path")

    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for bundle in journey.sources:
        path = output_dir / f"{bundle.source}.json"
        path.write_text(
            json.dumps(source_bundle_to_fhir(bundle), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        created.append(path)
    return tuple(created)
