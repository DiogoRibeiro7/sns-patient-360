"""Contract test for ingesting FHIR resources that reference a synthetic DICOM study."""

from sns_patient_360.imaging import build_imaging_fhir_resources, generate_synthetic_dx_study
from sns_patient_360.ingestion.validation import validate_bundle
from sns_patient_360.synthetic import generate_journey, source_bundle_to_fhir


def test_hospital_bundle_accepts_imaging_study_endpoint_and_report() -> None:
    journey = generate_journey(seed=360)
    hospital = next(bundle for bundle in journey.sources if bundle.source == "hospital")
    document = source_bundle_to_fhir(hospital)
    study = generate_synthetic_dx_study(
        patient_id=hospital.patient.source_patient_id,
        seed=360,
    )
    endpoint, imaging_study, report = build_imaging_fhir_resources(study)

    entries = document["entry"]
    assert isinstance(entries, list)
    entries.extend(
        [
            {"resource": endpoint},
            {"resource": imaging_study},
            {"resource": report},
        ]
    )

    source, patient_id, resources = validate_bundle(document)

    assert source == "hospital"
    assert patient_id == hospital.patient.source_patient_id
    assert {resource["resourceType"] for resource in resources} >= {
        "Endpoint",
        "ImagingStudy",
        "DiagnosticReport",
    }
