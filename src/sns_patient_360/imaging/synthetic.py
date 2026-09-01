"""Deterministic synthetic DICOM studies for imaging integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import (
    PYDICOM_IMPLEMENTATION_UID,
    DigitalXRayImageStorageForPresentation,
    ExplicitVRLittleEndian,
    generate_uid,
)

_UID_PREFIX = "1.2.826.0.1.3680043.8.498."


@dataclass(frozen=True)
class SyntheticDICOMStudy:
    """One deterministic single-instance synthetic DICOM imaging study."""

    patient_id: str
    study_instance_uid: str
    series_instance_uid: str
    sop_instance_uid: str
    modality: str
    study_datetime: datetime
    dicom_bytes: bytes


def _uid(*parts: object) -> str:
    """Create a deterministic DICOM UID from stable synthetic inputs."""
    return generate_uid(prefix=_UID_PREFIX, entropy_srcs=[str(part) for part in parts])


def _pixel_bytes(rows: int, columns: int, seed: int) -> bytes:
    """Generate a deterministic unsigned 8-bit grayscale test pattern."""
    return bytes(
        ((row * 5 + column * 3 + seed) % 256)
        for row in range(rows)
        for column in range(columns)
    )


def generate_synthetic_dx_study(
    *,
    patient_id: str = "HOSP-123456",
    seed: int = 360,
) -> SyntheticDICOMStudy:
    """Generate one deterministic synthetic chest DX study as valid DICOM bytes.

    The image is deliberately non-diagnostic: a small generated grayscale pattern used only
    to exercise DICOM storage, search and retrieval contracts.
    """
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not patient_id:
        raise ValueError("patient_id must be non-empty")

    study_uid = _uid("study", patient_id, seed)
    series_uid = _uid("series", patient_id, seed)
    sop_uid = _uid("instance", patient_id, seed)
    study_datetime = datetime(2026, 8, 20, 9, 30, 0)

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = DigitalXRayImageStorageForPresentation
    file_meta.MediaStorageSOPInstanceUID = sop_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID

    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = DigitalXRayImageStorageForPresentation
    dataset.SOPInstanceUID = sop_uid
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.PatientID = patient_id
    dataset.PatientName = "SYNTHETIC^PATIENT"
    dataset.PatientBirthDate = "19640417"
    dataset.PatientSex = "M"
    dataset.StudyDate = study_datetime.strftime("%Y%m%d")
    dataset.StudyTime = study_datetime.strftime("%H%M%S")
    dataset.ContentDate = dataset.StudyDate
    dataset.ContentTime = dataset.StudyTime
    dataset.Modality = "DX"
    dataset.StudyDescription = "Synthetic chest radiograph"
    dataset.SeriesDescription = "Synthetic PA chest"
    dataset.BodyPartExamined = "CHEST"
    dataset.StudyID = f"SYN{seed:04d}"
    dataset.SeriesNumber = 1
    dataset.InstanceNumber = 1
    dataset.Manufacturer = "SNS Patient 360 Synthetic Generator"
    dataset.ImageType = ["ORIGINAL", "PRIMARY"]
    dataset.PatientOrientation = ["A", "F"]

    dataset.Rows = 64
    dataset.Columns = 64
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = _pixel_bytes(dataset.Rows, dataset.Columns, seed)

    output = BytesIO()
    dataset.save_as(output, enforce_file_format=True)

    return SyntheticDICOMStudy(
        patient_id=patient_id,
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        sop_instance_uid=sop_uid,
        modality="DX",
        study_datetime=study_datetime,
        dicom_bytes=output.getvalue(),
    )
