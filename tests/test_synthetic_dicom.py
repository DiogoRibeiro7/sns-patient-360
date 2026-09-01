"""Tests for deterministic synthetic DICOM generation and FHIR linkage."""

from io import BytesIO

from pydicom import dcmread

from sns_patient_360.imaging import build_imaging_fhir_resources, generate_synthetic_dx_study


def test_synthetic_dicom_is_deterministic_and_parseable() -> None:
    first = generate_synthetic_dx_study(patient_id="HOSP-123456", seed=360)
    second = generate_synthetic_dx_study(patient_id="HOSP-123456", seed=360)

    assert first == second

    dataset = dcmread(BytesIO(first.dicom_bytes))
    assert dataset.PatientID == "HOSP-123456"
    assert dataset.Modality == "DX"
    assert dataset.StudyInstanceUID == first.study_instance_uid
    assert dataset.SeriesInstanceUID == first.series_instance_uid
    assert dataset.SOPInstanceUID == first.sop_instance_uid
    assert dataset.Rows == 64
    assert dataset.Columns == 64
    assert len(dataset.PixelData) == 64 * 64


def test_fhir_imaging_resources_reference_same_dicom_uids() -> None:
    study = generate_synthetic_dx_study(patient_id="HOSP-123456")
    endpoint, imaging_study, report = build_imaging_fhir_resources(study)

    assert endpoint["resourceType"] == "Endpoint"
    assert endpoint["connectionType"]["code"] == "dicom-wado-rs"
    assert endpoint["address"].endswith("/dicom-web/")

    assert imaging_study["resourceType"] == "ImagingStudy"
    assert imaging_study["subject"]["reference"] == "Patient/HOSP-123456"
    assert imaging_study["identifier"][0]["value"] == f"urn:oid:{study.study_instance_uid}"
    assert imaging_study["series"][0]["uid"] == study.series_instance_uid
    assert imaging_study["series"][0]["instance"][0]["uid"] == study.sop_instance_uid

    assert report["resourceType"] == "DiagnosticReport"
    assert report["imagingStudy"] == [{"reference": f"ImagingStudy/{imaging_study['id']}"}]
    assert "not diagnostic" in report["conclusion"].lower()
