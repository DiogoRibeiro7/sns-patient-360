"""FHIR resources that link Patient 360 to synthetic DICOM studies."""

from __future__ import annotations

from typing import Any

from sns_patient_360.imaging.synthetic import SyntheticDICOMStudy
from sns_patient_360.synthetic.export import SOURCE_URI_PREFIX, SYNTHETIC_TAG_SYSTEM

_DICOM_UID_SYSTEM = "urn:dicom:uid"


def _meta(source: str) -> dict[str, Any]:
    return {
        "source": f"{SOURCE_URI_PREFIX}{source}",
        "versionId": "1",
        "tag": [{"system": SYNTHETIC_TAG_SYSTEM, "code": "synthetic"}],
    }


def build_imaging_fhir_resources(
    study: SyntheticDICOMStudy,
    *,
    source: str = "hospital",
    endpoint_address: str = "http://orthanc:8042/dicom-web/",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build Endpoint, ImagingStudy and DiagnosticReport for one synthetic DICOM study."""
    endpoint_id = "dicomweb-orthanc"
    imaging_study_id = f"img-{study.study_instance_uid.split('.')[-1]}"
    report_id = f"report-{study.study_instance_uid.split('.')[-1]}"

    endpoint: dict[str, Any] = {
        "resourceType": "Endpoint",
        "id": endpoint_id,
        "status": "active",
        "connectionType": {
            "system": "http://terminology.hl7.org/CodeSystem/endpoint-connection-type",
            "code": "dicom-wado-rs",
        },
        "payloadType": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/endpoint-payload-type",
                        "code": "any",
                    }
                ]
            }
        ],
        "address": endpoint_address,
        "meta": _meta(source),
    }

    imaging_study: dict[str, Any] = {
        "resourceType": "ImagingStudy",
        "id": imaging_study_id,
        "status": "available",
        "subject": {"reference": f"Patient/{study.patient_id}"},
        "started": study.study_datetime.isoformat(),
        "identifier": [
            {
                "system": _DICOM_UID_SYSTEM,
                "value": f"urn:oid:{study.study_instance_uid}",
            }
        ],
        "modality": [
            {
                "system": "http://dicom.nema.org/resources/ontology/DCM",
                "code": study.modality,
            }
        ],
        "endpoint": [{"reference": f"Endpoint/{endpoint_id}"}],
        "numberOfSeries": 1,
        "numberOfInstances": 1,
        "series": [
            {
                "uid": study.series_instance_uid,
                "number": 1,
                "modality": {
                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                    "code": study.modality,
                },
                "numberOfInstances": 1,
                "instance": [
                    {
                        "uid": study.sop_instance_uid,
                        "sopClass": {
                            "system": _DICOM_UID_SYSTEM,
                            "code": "1.2.840.10008.5.1.4.1.1.1.1",
                        },
                        "number": 1,
                    }
                ],
            }
        ],
        "meta": _meta(source),
    }

    diagnostic_report: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": report_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "RAD",
                    }
                ]
            }
        ],
        "code": {"text": "Synthetic chest radiograph report"},
        "subject": {"reference": f"Patient/{study.patient_id}"},
        "effectiveDateTime": study.study_datetime.isoformat(),
        "imagingStudy": [{"reference": f"ImagingStudy/{imaging_study_id}"}],
        "conclusion": "Synthetic study for interoperability testing only; not diagnostic.",
        "meta": _meta(source),
    }

    return endpoint, imaging_study, diagnostic_report
