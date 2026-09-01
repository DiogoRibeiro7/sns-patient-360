"""Opt-in end-to-end DICOMweb integration test against the local Orthanc stack."""

from __future__ import annotations

import os

import pytest

from sns_patient_360.imaging import DICOMwebClient, generate_synthetic_dx_study

pytestmark = pytest.mark.integration


def test_stow_qido_wado_round_trip_against_orthanc() -> None:
    if os.getenv("SNS360_DICOMWEB_INTEGRATION") != "1":
        pytest.skip("Set SNS360_DICOMWEB_INTEGRATION=1 with Orthanc running")

    study = generate_synthetic_dx_study(patient_id="HOSP-123456", seed=360)
    with DICOMwebClient(
        "http://127.0.0.1:8042/dicom-web",
        username="sns360",
        password="sns360-orthanc-dev-only",
    ) as client:
        client.store_instance(study.dicom_bytes)
        matches = client.search_studies(study.study_instance_uid)
        retrieved = client.retrieve_instance(
            study_instance_uid=study.study_instance_uid,
            series_instance_uid=study.series_instance_uid,
            sop_instance_uid=study.sop_instance_uid,
        )

    assert matches
    assert retrieved
