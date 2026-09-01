# Clinical ingestion, imaging and persistence

## Scope

SNS Patient 360 has multiple authoritative data planes because clinical documents and diagnostic imaging have different storage and protocol semantics.

- FHIR clinical documents use PostgreSQL + MongoDB.
- Diagnostic images use DICOM/DICOMweb + PACS/VNA + object storage.
- Redis stores only rebuildable Patient 360 projections.

## Clinical FHIR ingestion

```mermaid
sequenceDiagram
    autonumber
    participant Source as Source FHIR Bundle
    participant Validator as FHIR Validator
    participant Resolver as Identity Resolver
    participant SQL as PostgreSQL Identity / Audit Store
    participant Mongo as MongoDB FHIR Document Store
    participant Ledger as Ingestion Event Ledger

    Source->>Validator: Submit FHIR Bundle
    Validator->>Validator: Validate resource shape and source semantics

    alt Bundle invalid
        Validator->>Ledger: Append rejected event
    else Bundle valid
        Validator->>Resolver: Source-local Patient + shared identifier
        Resolver->>SQL: Resolve/create canonical patient and alias
        loop Every resource version, including safe replay
            Validator->>Mongo: Atomic source-version upsert
        end
        SQL->>Ledger: Mark accepted or partial/recovery state
    end
```

## Imaging ingestion

```mermaid
sequenceDiagram
    autonumber
    participant Modality as Imaging Modality
    participant DICOM as DICOM/DICOMweb Gateway
    participant PACS as PACS/VNA
    participant Object as S3-compatible Object Storage
    participant FHIR as FHIR Clinical Layer

    Modality->>DICOM: DICOM C-STORE / STOW-RS
    DICOM->>PACS: Register study / series / instances
    PACS->>Object: Store DICOM objects
    PACS->>FHIR: Associate ImagingStudy / Endpoint metadata
    FHIR->>FHIR: Link DiagnosticReport where available
```

The Patient 360 service does not write DICOM files directly to object storage. The PACS/VNA owns DICOM lifecycle and object-storage interaction.

## Authoritative data-plane architecture

```mermaid
flowchart TB
    FHIRAPI[FHIR Ingestion Service]
    DICOM[DICOM / DICOMweb Gateway]
    STATE[Patient State Engine]
    API[Patient 360 API]

    PG[(PostgreSQL)]
    MONGO[(MongoDB)]
    PACS[(PACS / VNA)]
    OBJECT[(Object Storage)]
    REDIS[(Redis)]

    FHIRAPI --> PG
    FHIRAPI --> MONGO

    DICOM --> PACS
    PACS --> OBJECT

    PG --> STATE
    MONGO --> STATE
    PACS --> STATE

    STATE --> REDIS
    STATE --> API
    REDIS --> API

    PG -. identity / aliases / consent / audit metadata .-> PG
    MONGO -. complete versioned FHIR documents .-> MONGO
    PACS -. DICOM catalogue / UIDs / lifecycle .-> PACS
    OBJECT -. DICOM bulk binary objects .-> OBJECT
    REDIS -. disposable projections only .-> REDIS
```

### PostgreSQL responsibility

PostgreSQL owns data with strong relational constraints: canonical patient identity, source aliases, consent/access metadata, ingestion coordination and audit metadata.

### MongoDB responsibility

MongoDB owns complete FHIR clinical source documents and reports, preserving nested FHIR structure and source versions. It may contain `ImagingStudy`, `Endpoint` and `DiagnosticReport` resources, but not authoritative diagnostic image pixels.

### PACS/VNA responsibility

The PACS/VNA owns DICOM study, series and instance cataloguing, DICOM UIDs, image lifecycle, DICOM/DICOMweb operations and retrieval semantics.

### Object-storage responsibility

S3-compatible object storage owns large DICOM binary objects behind the PACS/VNA. Patient 360 application services must not make clinical decisions or viewer links from raw bucket/object keys.

### Redis responsibility

Redis contains only rebuildable Patient 360 projections and cache entries. Redis loss must not cause loss of clinical documents or DICOM studies.

## Patient identity across clinical and imaging planes

```mermaid
flowchart LR
    FHIRPAT[Source FHIR Patient]
    DICOMPT[DICOM Patient / Study identifiers]
    RESOLVE[Canonical Identity Resolution]
    CANON[Canonical Patient ID]

    FHIRPAT --> RESOLVE
    DICOMPT --> RESOLVE
    RESOLVE --> CANON

    CANON --> PG[(PostgreSQL aliases)]
    CANON --> MONGO[(FHIR documents)]
    CANON --> PACS[(Imaging study references)]
```

The synthetic reference implementation starts from deterministic identifiers. More complex patient matching must be introduced explicitly and must not silently merge uncertain identities.

## Cross-database recovery

PostgreSQL and MongoDB do not share a single ACID transaction. Clinical ingestion therefore uses deterministic source-version keys, partial-ingestion state, idempotent replay and reconciliation.

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Validated: FHIR validation succeeds
    Received --> Rejected: validation fails
    Validated --> IdentityCommitted
    IdentityCommitted --> DocumentsCommitted
    DocumentsCommitted --> Committed
    IdentityCommitted --> RecoveryRequired: Mongo write interrupted
    RecoveryRequired --> DocumentsCommitted: safe replay
    Rejected --> [*]
    Committed --> [*]
```

The DICOM/PACS/object-storage plane has its own storage lifecycle. A bulk-storage outage may temporarily prevent image retrieval, but it must not corrupt PostgreSQL identity data or MongoDB clinical documents.

## Local development

`docker-compose.yml` provides:

- PostgreSQL for relational identity/governance state;
- MongoDB for FHIR documents;
- Redis for disposable projection caching;
- Orthanc as the reference PACS/DICOMweb gateway;
- MinIO as S3-compatible DICOM bulk storage behind Orthanc.

Published development ports bind to loopback. Default CI remains independent of external clinical services; dedicated integration tests can exercise the real Docker services.

## Patient State Engine boundary

```mermaid
flowchart LR
    PG[(PostgreSQL Identity)]
    MONGO[(MongoDB FHIR)]
    PACS[(PACS Imaging Catalogue)]
    ENGINE[Patient State Engine]
    REDIS[(Redis Cache)]
    READ[Patient 360 API]

    PG --> ENGINE
    MONGO --> ENGINE
    PACS --> ENGINE
    ENGINE --> REDIS
    ENGINE --> READ
```

The Patient State Engine consumes metadata and references from the imaging plane. It must not download DICOM pixel payloads merely to construct the Patient 360 summary or timeline.
