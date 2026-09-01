# Diagnostic imaging functional and non-functional requirements

This document extends the baseline requirements in `requirements.md` for the diagnostic-imaging plane. These IDs are stable requirement references for future imaging implementation PRs and tests.

# Functional requirements

## Study representation and linkage

### FR-070 — Imaging study representation
The system MUST represent supported diagnostic imaging studies in the longitudinal clinical record using FHIR `ImagingStudy` or an explicitly documented compatible profile.

**Acceptance criteria**
- the study is associated with the canonical patient;
- modality and study date are available when supplied by the source;
- the DICOM Study Instance UID is preserved;
- the study can link to its diagnostic report and retrieval endpoint.

### FR-071 — DICOM identifier preservation
The imaging integration MUST preserve DICOM identifiers required to resolve studies, series and instances.

At minimum, when available, this includes:
- Study Instance UID;
- Series Instance UID;
- SOP Instance UID.

### FR-072 — Diagnostic report linkage
A radiology or imaging `DiagnosticReport` MUST be linkable to the imaging study it interprets without copying DICOM pixel payloads into the FHIR document store.

### FR-073 — DICOMweb study discovery
An authorised clinician-facing imaging workflow MUST be able to discover studies/series/instances using the DICOMweb query boundary (QIDO-RS).

### FR-074 — DICOMweb image retrieval
An authorised imaging viewer MUST retrieve source DICOM studies, series, instances or frames through the DICOMweb retrieval boundary (WADO-RS).

### FR-075 — DICOMweb storage
The reference imaging integration SHOULD support ingestion of synthetic DICOM objects through STOW-RS. Traditional DICOM C-STORE MAY also be supported by the PACS/VNA.

### FR-076 — Imaging timeline integration
Patient 360 MUST be able to surface an imaging study as a longitudinal event without loading image pixels into the Patient 360 projection.

**Acceptance criteria**
- study metadata can appear in the timeline;
- linked report status/conclusion can be surfaced where authorised;
- opening images hands off to an authorised DICOM viewer/retrieval flow.

### FR-077 — Imaging provenance
Each Patient 360 imaging reference MUST retain enough provenance to identify the source imaging system/PACS and the FHIR/DICOM identifiers supporting the derived item.

### FR-078 — Imaging access audit
Access to diagnostic images through the Patient 360 workflow MUST generate an auditable event with actor, patient/study scope, time, action and outcome.

### FR-079 — No direct application object-store access
Patient 360 application services MUST NOT treat S3/MinIO object keys as the clinical imaging API. Retrieval and storage of diagnostic images MUST pass through the PACS/VNA/DICOM boundary.

# Non-functional requirements

## Imaging interoperability

### NFR-100 — DICOM interoperability boundary
DICOM/DICOMweb MUST be the interoperability boundary for diagnostic image objects and imaging study hierarchy.

### NFR-101 — FHIR/DICOM separation
FHIR/MongoDB MUST contain imaging metadata, clinical relationships and reports, not authoritative diagnostic pixel payloads.

### NFR-102 — PACS/VNA ownership
The PACS/VNA MUST own study, series and instance lifecycle and DICOM identifiers. Object storage alone MUST NOT be treated as a PACS.

### NFR-103 — Bulk-storage abstraction
Object storage MUST remain behind the PACS/VNA storage boundary. Changing the underlying S3-compatible implementation SHOULD NOT require Patient 360 clinical APIs to change.

## Security and privacy

### NFR-110 — Authorised image retrieval
DICOMweb retrieval exposed through a Patient 360 workflow MUST require an authorised context appropriate to the actor, role, purpose and applicable consent policy.

### NFR-111 — Imaging access logging
Study and image retrieval events MUST be auditable without placing diagnostic pixel payloads in routine application logs.

### NFR-112 — Imaging service network boundary
Local PACS, DICOMweb and object-storage management ports MUST bind to loopback only when published to the development host unless explicitly documented otherwise.

### NFR-113 — Imaging secrets
PACS/object-storage credentials MUST NOT be committed as production secrets. Development-only credentials MAY exist in the local reference stack when clearly labelled and isolated to loopback/local Docker networking.

## Reliability and integrity

### NFR-120 — Imaging UID integrity
The system MUST NOT rewrite DICOM Study/Series/SOP Instance UIDs during Patient 360 projection derivation.

### NFR-121 — Pixel fidelity
Patient 360 processing MUST NOT alter authoritative DICOM pixel data. Rendered derivatives MAY be used for user-interface convenience but MUST NOT replace the source DICOM object.

### NFR-122 — Imaging recovery
Loss of Redis or Patient 360 projections MUST NOT cause loss of DICOM studies. Imaging projections must be rebuildable from FHIR metadata plus the PACS/VNA catalogue.

### NFR-123 — Object-store failure isolation
Temporary unavailability of bulk object storage MUST NOT corrupt FHIR clinical documents or relational patient identity metadata. Imaging retrieval may be unavailable until the PACS/object-store path recovers.

## Performance and scalability

### NFR-130 — Metadata before pixels
Patient summary/timeline requests SHOULD retrieve imaging metadata without downloading DICOM pixel payloads.

### NFR-131 — Streaming/bounded retrieval
Imaging retrieval MUST use DICOM/PACS mechanisms appropriate for large studies and MUST NOT require loading an entire multi-instance study into Patient 360 application memory merely to display study metadata.

## Testability

### NFR-140 — Synthetic DICOM only
Repository fixtures and automated tests MUST use synthetic/de-identified generated DICOM data and MUST NOT depend on real patient imaging.

### NFR-141 — Local imaging stack
A dedicated integration environment SHOULD be reproducible with Docker Compose using a DICOMweb-capable reference PACS and S3-compatible object storage.

# Implementation gate for the imaging milestone

The first executable imaging milestone should verify at minimum:

- FR-070, FR-071, FR-072, FR-073, FR-074, FR-076, FR-077;
- NFR-100, NFR-101, NFR-102, NFR-103;
- NFR-110, NFR-112;
- NFR-120, NFR-122, NFR-130, NFR-140.
