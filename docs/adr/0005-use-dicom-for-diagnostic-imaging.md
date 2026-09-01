# ADR 0005 — Use DICOM/DICOMweb for diagnostic imaging

- Status: Accepted
- Date: 2026-09-01

## Context

SNS Patient 360 must represent diagnostic imaging such as X-ray, CT, MRI and ultrasound. These payloads are fundamentally different from ordinary clinical documents: one study can contain many series and hundreds or thousands of image instances and frames, together with DICOM-specific identifiers, transfer syntaxes and retrieval semantics.

Storing diagnostic image binaries as MongoDB documents or GridFS objects would make the application responsible for reimplementing imaging lifecycle, study/series/instance semantics and viewer retrieval behaviour.

## Decision

1. HL7 FHIR remains the clinical interoperability layer for imaging metadata and clinical relationships.
2. FHIR `ImagingStudy` represents the imaging study in the longitudinal clinical record.
3. FHIR `DiagnosticReport` represents the clinical interpretation/report and may reference the corresponding imaging study.
4. DICOM/DICOMweb is the authoritative protocol boundary for diagnostic image storage, discovery and retrieval.
5. A PACS/VNA owns DICOM study, series and instance lifecycle and identifiers.
6. Large DICOM binary objects are stored behind the PACS/VNA in bulk/object storage; Patient 360 does not access object storage directly.
7. QIDO-RS, WADO-RS and STOW-RS are the web-facing imaging operations for search, retrieval and storage.
8. Redis may cache derived imaging projections but is never authoritative.

## Local reference architecture

Orthanc is selected as the reference local PACS/DICOMweb server because it provides DICOMweb support and a small deployable footprint. MinIO is selected as the S3-compatible local object-storage implementation. Orthanc's object-storage plugin boundary allows an S3-compatible backend such as MinIO while keeping Patient 360 isolated from raw storage details.

## Consequences

### Positive

- DICOM image semantics remain in a DICOM-native system.
- Patient 360 does not become an accidental PACS implementation.
- Imaging studies can participate in the clinical timeline through FHIR without copying pixels into MongoDB.
- Image viewers can use standard DICOMweb retrieval.
- Bulk storage can scale independently from FHIR clinical document storage.

### Negative

- The platform gains another persistent subsystem and interoperability standard.
- Imaging identity/provenance must be reconciled with the canonical patient identity.
- Backup, access control, audit and recovery must cover PACS/VNA and object storage in addition to PostgreSQL/MongoDB.

## Rejected alternatives

### Store DICOM binaries in MongoDB/GridFS

Rejected because this pushes imaging lifecycle, study hierarchy, frame retrieval and DICOM semantics into the application/document database.

### Store raw DICOM files directly in S3/MinIO from Patient 360

Rejected because object storage alone is not a PACS/VNA and does not provide the DICOM catalogue, UIDs, lifecycle or DICOMweb retrieval contract.

### Store rendered PNG/JPEG only

Rejected as an authoritative representation because rendered images lose DICOM metadata, diagnostic precision and study/series/instance semantics. Rendered representations may be generated for UI convenience but cannot replace source DICOM objects.
