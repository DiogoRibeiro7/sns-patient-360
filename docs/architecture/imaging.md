# Diagnostic imaging architecture

## Purpose

Diagnostic images are not ordinary clinical documents. SNS Patient 360 therefore separates the **clinical relationship to imaging** from the **DICOM objects that contain the diagnostic image data**.

FHIR resources describe why an imaging study exists, how it relates to the patient and report, and where it can be retrieved. DICOM/DICOMweb owns the imaging study, series, instances, frames and pixel data.

## Imaging boundary

```mermaid
flowchart LR
    MODALITY[Imaging Modality\nCT / MR / US / CR / DX]
    DICOM[DICOM / DICOMweb Gateway]
    PACS[(PACS / VNA)]
    OBJECT[(S3-compatible Object Storage)]

    FHIR[FHIR Clinical Layer]
    IMGSTUDY[ImagingStudy]
    REPORT[DiagnosticReport]
    ENDPOINT[Endpoint]
    P360[Patient 360]
    VIEWER[DICOM Viewer]

    MODALITY -->|DICOM / STOW-RS| DICOM
    DICOM --> PACS
    PACS --> OBJECT

    PACS -->|Study / series metadata| IMGSTUDY
    REPORT --> IMGSTUDY
    IMGSTUDY --> ENDPOINT

    IMGSTUDY --> FHIR
    REPORT --> FHIR
    FHIR --> P360

    P360 -->|Authorised imaging reference| VIEWER
    VIEWER -->|QIDO-RS / WADO-RS| DICOM
```

The Patient 360 application never writes arbitrary DICOM files directly to object storage. The PACS/VNA is responsible for imaging lifecycle and storage semantics.

## DICOMweb operations

The imaging service boundary uses DICOMweb operations:

- **QIDO-RS** for study, series and instance search;
- **WADO-RS** for retrieval of studies, series, instances, frames, metadata and rendered representations;
- **STOW-RS** for storage of DICOM studies/instances into the imaging system.

```mermaid
sequenceDiagram
    autonumber
    participant Modality as Imaging Source
    participant Gateway as DICOMweb Gateway
    participant PACS as PACS/VNA
    participant Object as Object Storage
    participant FHIR as FHIR Layer
    participant P360 as Patient 360
    participant Viewer as DICOM Viewer

    Modality->>Gateway: STOW-RS / DICOM C-STORE
    Gateway->>PACS: Register study / series / instances
    PACS->>Object: Persist DICOM binary objects
    PACS->>FHIR: Publish/associate ImagingStudy metadata
    FHIR->>P360: Make study/report visible in patient timeline
    P360->>Viewer: Open authorised study
    Viewer->>Gateway: QIDO-RS search
    Viewer->>Gateway: WADO-RS retrieve images/frames
    Gateway->>PACS: Resolve requested DICOM objects
    PACS->>Object: Read binary objects
    Object-->>PACS: DICOM object bytes
    PACS-->>Viewer: DICOMweb response
```

## Executable synthetic imaging path

The first executable imaging milestone uses a deterministic synthetic DX study. The DICOM and FHIR planes share the same patient and DICOM UIDs.

```mermaid
flowchart LR
    GEN[Synthetic DICOM Generator]
    DCM[Deterministic DX Instance]
    STOW[STOW-RS]
    ORTHANC[(Orthanc PACS)]
    MINIO[(MinIO Object Storage)]
    QIDO[QIDO-RS Search]
    WADO[WADO-RS Retrieve]

    FHIRGEN[FHIR Imaging Link Builder]
    ENDPOINT[Endpoint]
    IMG[ImagingStudy]
    REPORT[DiagnosticReport]
    INGEST[FHIR Ingestion Boundary]

    GEN --> DCM
    DCM --> STOW
    STOW --> ORTHANC
    ORTHANC --> MINIO
    ORTHANC --> QIDO
    ORTHANC --> WADO

    GEN --> FHIRGEN
    FHIRGEN --> ENDPOINT
    FHIRGEN --> IMG
    FHIRGEN --> REPORT
    ENDPOINT --> INGEST
    IMG --> INGEST
    REPORT --> INGEST

    DCM -. same Study / Series / SOP UIDs .-> IMG
```

```mermaid
sequenceDiagram
    autonumber
    participant Test as Integration Test
    participant Generator as Synthetic DICOM Generator
    participant Orthanc as Orthanc DICOMweb
    participant MinIO as MinIO
    participant FHIR as FHIR Builder / Validator

    Test->>Generator: Generate deterministic DX study
    Generator-->>Test: DICOM bytes + Study/Series/SOP UIDs
    Test->>Orthanc: STOW-RS instance
    Orthanc->>MinIO: Persist DICOM object
    Test->>Orthanc: QIDO-RS by Study Instance UID
    Orthanc-->>Test: Matching study metadata
    Test->>Orthanc: WADO-RS instance retrieval
    Orthanc-->>Test: DICOM response
    Test->>FHIR: Build Endpoint + ImagingStudy + DiagnosticReport
    FHIR-->>Test: Resources linked to same patient and UIDs
```

Normal unit tests validate deterministic DICOM generation, FHIR UID linkage and DICOMweb request semantics using an injected HTTP transport. A dedicated `DICOM Integration` workflow starts the real Orthanc/MinIO stack and executes STOW → QIDO → WADO.

## FHIR relationship

`ImagingStudy` is the FHIR representation of the study relationship and DICOM identifiers. `DiagnosticReport` carries the clinical interpretation/report and may reference the study. `Endpoint` provides retrieval connection information where appropriate.

Patient 360 may expose:

- study date;
- modality;
- description / body site when available;
- Study Instance UID;
- series metadata;
- study status;
- linked diagnostic report;
- authorised viewer/retrieval endpoint;
- provenance.

Patient 360 MUST NOT treat the DICOM pixel payload as a MongoDB/FHIR document field.

## Storage responsibilities

```mermaid
flowchart TB
    PG[(PostgreSQL)]
    MONGO[(MongoDB)]
    PACS[(PACS / VNA)]
    OBJECT[(Object Storage)]
    REDIS[(Redis)]

    PG --- PGROLE[Identity / aliases / consent / audit metadata]
    MONGO --- MONGOROLE[FHIR resources / reports / imaging metadata]
    PACS --- PACSROLE[DICOM catalogue / UIDs / study-series-instance lifecycle]
    OBJECT --- OBJROLE[Large binary DICOM objects]
    REDIS --- REDISROLE[Disposable Patient 360 projections]
```

Object storage is an implementation detail behind the PACS/VNA boundary. The reference local stack uses an S3-compatible service to model that bulk-storage role.

## Imaging provenance

Imaging references must preserve enough information to answer:

1. Which patient/canonical identity is this study associated with?
2. Which source organisation/system supplied it?
3. What are the DICOM Study/Series/SOP Instance UIDs?
4. Which FHIR `ImagingStudy` and `DiagnosticReport` describe it?
5. Which endpoint/PACS is authoritative for retrieval?
6. Who accessed the imaging study and for what purpose?

## Security boundary

```mermaid
flowchart LR
    USER[Clinician]
    AUTH[Authentication]
    POLICY[Role / consent / purpose policy]
    P360[Patient 360 API]
    VIEWER[DICOM Viewer]
    DICOM[DICOMweb Gateway]
    AUDIT[(Audit Ledger)]

    USER --> AUTH
    AUTH --> POLICY
    POLICY --> P360
    P360 -->|Study reference + authorised viewer context| VIEWER
    VIEWER --> DICOM
    P360 --> AUDIT
    VIEWER --> AUDIT
```

The viewer and DICOMweb gateway must not be reachable through an unauthorised Patient 360 link. Production architecture must authenticate/authorise image retrieval and audit access to studies.

## Local reference implementation

The local imaging stack is:

- **Orthanc** as the reference PACS/DICOMweb service;
- **MinIO** as S3-compatible bulk object storage;
- DICOMweb enabled on Orthanc;
- a deterministic synthetic DICOM generator for tests;
- a small application-side DICOMweb client for STOW-RS, QIDO-RS and WADO-RS;
- optional web viewer support later.

The architecture deliberately keeps PACS/VNA and object storage as separate concepts even when they run in the same local Docker Compose environment.

## Out of scope for this milestone

- production SNS imaging integration;
- real DICOM patient data;
- diagnostic AI over image pixels;
- automated radiology interpretation;
- full modality worklist implementation;
- pathology/whole-slide imaging semantics beyond noting that they may require additional specialised profiles.
