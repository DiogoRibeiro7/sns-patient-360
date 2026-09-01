"""Small DICOMweb client for synthetic imaging integration."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx


class DICOMwebClient:
    """Access a PACS/VNA through STOW-RS, QIDO-RS and WADO-RS only."""

    def __init__(
        self,
        base_url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must be non-empty")
        self._base_url = base_url.rstrip("/")
        auth = None
        if username is not None or password is not None:
            if username is None or password is None:
                raise ValueError("username and password must be provided together")
            auth = httpx.BasicAuth(username, password)
        self._owns_client = client is None
        self._client = client or httpx.Client(auth=auth, timeout=30.0)

    def close(self) -> None:
        """Close the underlying client when it was created internally."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> DICOMwebClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def store_instance(self, dicom_bytes: bytes) -> None:
        """Store one DICOM instance through STOW-RS."""
        if not dicom_bytes:
            raise ValueError("dicom_bytes must be non-empty")
        boundary = f"sns360-{uuid4().hex}"
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/dicom\r\n\r\n"
        ).encode() + dicom_bytes + f"\r\n--{boundary}--\r\n".encode()
        response = self._client.post(
            f"{self._base_url}/studies",
            content=body,
            headers={
                "Content-Type": f'multipart/related; type="application/dicom"; boundary={boundary}',
                "Accept": "application/dicom+json, application/json",
            },
        )
        response.raise_for_status()

    def search_studies(self, study_instance_uid: str) -> tuple[dict[str, Any], ...]:
        """Search studies by DICOM Study Instance UID through QIDO-RS."""
        if not study_instance_uid:
            raise ValueError("study_instance_uid must be non-empty")
        response = self._client.get(
            f"{self._base_url}/studies",
            params={"StudyInstanceUID": study_instance_uid},
            headers={"Accept": "application/dicom+json"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("QIDO-RS response must be a JSON array")
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError("QIDO-RS response entries must be JSON objects")
        return tuple(payload)

    def retrieve_instance(
        self,
        *,
        study_instance_uid: str,
        series_instance_uid: str,
        sop_instance_uid: str,
    ) -> bytes:
        """Retrieve one DICOM instance through WADO-RS."""
        identifiers = (study_instance_uid, series_instance_uid, sop_instance_uid)
        if not all(identifiers):
            raise ValueError("study, series and SOP instance UIDs must be non-empty")
        response = self._client.get(
            (
                f"{self._base_url}/studies/{study_instance_uid}"
                f"/series/{series_instance_uid}/instances/{sop_instance_uid}"
            ),
            headers={"Accept": 'multipart/related; type="application/dicom"'},
        )
        response.raise_for_status()
        if not response.content:
            raise ValueError("WADO-RS returned an empty response")
        return response.content
