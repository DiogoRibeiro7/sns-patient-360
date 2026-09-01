"""Protocol tests for the small DICOMweb client."""

from __future__ import annotations

import json

import httpx

from sns_patient_360.imaging.dicomweb import DICOMwebClient


def test_stow_qido_and_wado_paths_and_headers() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            assert request.url.path == "/dicom-web/studies"
            assert request.headers["content-type"].startswith("multipart/related")
            assert b"application/dicom" in request.content
            return httpx.Response(200, json={})
        if request.url.path == "/dicom-web/studies":
            assert request.url.params["StudyInstanceUID"] == "1.2.3"
            assert request.headers["accept"] == "application/dicom+json"
            return httpx.Response(200, content=json.dumps([{"0020000D": {"Value": ["1.2.3"]}}]))
        assert request.url.path == "/dicom-web/studies/1.2.3/series/1.2.4/instances/1.2.5"
        assert "application/dicom" in request.headers["accept"]
        return httpx.Response(200, content=b"multipart-dicom-response")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    dicomweb = DICOMwebClient("http://orthanc:8042/dicom-web", client=client)

    dicomweb.store_instance(b"DICM-synthetic")
    studies = dicomweb.search_studies("1.2.3")
    retrieved = dicomweb.retrieve_instance(
        study_instance_uid="1.2.3",
        series_instance_uid="1.2.4",
        sop_instance_uid="1.2.5",
    )

    assert len(studies) == 1
    assert retrieved == b"multipart-dicom-response"
    assert [request.method for request in requests] == ["POST", "GET", "GET"]


def test_credentials_must_be_supplied_together() -> None:
    try:
        DICOMwebClient("http://example.invalid", username="user")
    except ValueError as exc:
        assert "together" in str(exc)
    else:
        raise AssertionError("Expected incomplete credentials to be rejected")
