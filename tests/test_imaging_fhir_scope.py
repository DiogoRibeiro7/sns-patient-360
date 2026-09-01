"""Contract tests for the staged FHIR imaging resource boundary."""

from sns_patient_360.ingestion.validation import validate_bundle
from sns_patient_360.synthetic.export import (
    SOURCE_URI_PREFIX,
    SYNTHETIC_IDENTIFIER_SYSTEM,
    SYNTHETIC_TAG_SYSTEM,
)


def _meta() -> dict[str, object]:
    """Return synthetic source metadata used by imaging-scope fixtures."""
    return {
        "source": f"{SOURCE_URI_PREFIX}hospital",
        "versionId": "1",
        "tag": [{"system": SYNTHETIC_TAG_SYSTEM, "code": "synthetic"}],
    }


def test_imaging_study_and_endpoint_are_validated_with_distinct_scopes() -> None:
    """ImagingStudy is patient-scoped while Endpoint is service infrastructure metadata."""
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "HOSP-123456",
                    "meta": _meta(),
                    "identifier": [
                        {
                            "system": SYNTHETIC_IDENTIFIER_SYSTEM,
                            "value": "SNS-SYN-123456",
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Endpoint",
                    "id": "dicomweb-endpoint",
                    "meta": _meta(),
                    "status": "active",
                    "address": "http://orthanc:8042/dicom-web/",
                }
            },
            {
                "resource": {
                    "resourceType": "ImagingStudy",
                    "id": "study-1",
                    "meta": _meta(),
                    "status": "available",
                    "subject": {"reference": "Patient/HOSP-123456"},
                    "identifier": [
                        {
                            "system": "urn:dicom:uid",
                            "value": "urn:oid:1.2.826.0.1.3680043.10.360.1",
                        }
                    ],
                    "endpoint": [{"reference": "Endpoint/dicomweb-endpoint"}],
                }
            },
        ],
    }

    source, patient_id, resources = validate_bundle(bundle)

    assert source == "hospital"
    assert patient_id == "HOSP-123456"
    assert {resource["resourceType"] for resource in resources} == {
        "Patient",
        "Endpoint",
        "ImagingStudy",
    }
