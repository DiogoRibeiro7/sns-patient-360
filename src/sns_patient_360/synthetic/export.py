"""Export deterministic synthetic source bundles as FHIR-shaped JSON documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sns_patient_360.synthetic.models import SyntheticJourney, SyntheticSourceBundle


def source_bundle_to_fhir(bundle: SyntheticSourceBundle) -> dict[str, Any]:
    """Convert one source bundle into a minimal FHIR Bundle-shaped document."""
    entries: list[dict[str, Any]] = []
    for resource in bundle.resources:
        fhir_resource: dict[str, Any] = {
            "resourceType": resource.resource_type,
            "id": resource.resource_id,
            "subject": {"reference": f"Patient/{bundle.patient.source_patient_id}"},
            "meta": {
                "source": bundle.source,
                "tag": [
                    {
                        "system": "https://example.invalid/sns-patient-360/synthetic",
                        "code": "synthetic",
                    }
                ],
            },
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
            "value": f"{bundle.source}-{bundle.patient.synthetic_master_id}",
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
