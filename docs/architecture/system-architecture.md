# System architecture

## Purpose

SNS Patient 360 reconstructs a unified longitudinal patient view from fragmented clinical source systems while preserving clinical meaning, provenance, consent context and auditability.

The platform does not replace source clinical systems. HL7 FHIR is the clinical interoperability boundary. DICOM/DICOMweb is the diagnostic-imaging interoperability boundary. Patient 360 is a derived read model optimised for clinician and patient-facing queries.

All architecture diagrams in this repository are expressed as Mermaid inside versioned Markdown documents.

## Architectural principles

1. **FHIR remains the clinical source/interchange truth.** Patient 360 does not redefine source clinical semantics.
2. **DICOM remains the diagnostic-imaging truth.** Image pixels and DICOM lifecycle do not belong in MongoDB or the Patient 360 read model.
3. **Derived state is traceable.** Every derived Patient 360 item must link to its supporting FHIR and/or imaging source.
4. **Conflicts are preserved.** Conflicting or superseded clinical facts must not be silently overwritten.
5. **Clinical state is temporal.** Current state and historical facts are distinct concepts.
6. **Access is auditable.** Reads, transformations and imaging retrieval must be attributable.
7. **Synthetic data only.** The reference implementation must not contain real patient data.
8. **AI is not part of the clinical truth layer.** Diagnosis and autonomous treatment recommendations are out of scope.

## System context

```mermaid
flowchart LR
    PC[Primary Care System]
    HOSP[Hospital System]
    LAB[Laboratory System]
    PHARM[Pharmacy System]
    MOD[Imaging Modalities]

    P360[SNS Patient 360]
    PACS[PACS / VNA]
    CLINICIAN[Clinician]
    PATIENT[Patient]
    AUDITOR[Auditor / Security Reviewer]

    PC -->|FHIR| P360
    HOSP -->|FHIR| P360
    LAB -->|FHIR| P360
    PHARM -->|FHIR| P360
    MOD -->|DICOM| PACS
    PACS -->|DICOMweb + imaging references| P360

    P360 -->|Longitudinal clinical view| CLINICIAN
    P360 -->|Patient-facing health view| PATIENT
    P360 -->|Access and provenance records| AUDITOR
```

## Logical architecture

```mermaid
flowchart TB
    subgraph Sources[Clinical source systems]
        PC[Primary Care]
        HOSP[Hospital]
        LAB[Laboratory]
        PHARM[Pharmacy]
        MOD[Imaging Modalities]
    end

    subgraph Interop[Interoperability boundaries]
        FHIRAPI[FHIR API]
        VALIDATE[FHIR Validation / Normalisation]
        DICOM[DICOM / DICOMweb Gateway]
    end

    subgraph Truth[Authoritative data planes]
        PG[(PostgreSQL\nIdentity / governance metadata)]
        MONGO[(MongoDB\nVersioned FHIR documents)]
        PACS[(PACS / VNA\nDICOM catalogue)]
        OBJECT[(S3-compatible Object Storage\nDICOM bulk objects)]
    end

    subgraph ReadModel[Patient 360 layer]
        STATE[Patient State Engine]
        REDIS[(Redis\nDisposable projection cache)]
    end

    subgraph Experience[Experience layer]
        API[Patient 360 API]
        CLINWEB[Clinician Web]
        PATWEB[Patient Web]
        VIEWER[DICOM Viewer]
    end

    PC --> FHIRAPI
    HOSP --> FHIRAPI
    LAB --> FHIRAPI
    PHARM --> FHIRAPI
    HOSP --> DICOM
    MOD --> DICOM

    FHIRAPI --> VALIDATE
    VALIDATE --> PG
    VALIDATE --> MONGO

    DICOM --> PACS
    PACS --> OBJECT

    PG --> STATE
    MONGO --> STATE
    PACS --> STATE
    STATE --> REDIS
    STATE --> API
    REDIS --> API

    API --> CLINWEB
    API --> PATWEB
    CLINWEB --> VIEWER
    VIEWER --> DICOM
```

## Clinical ingestion and derivation

```mermaid
sequenceDiagram
    autonumber
    participant Source as Clinical Source
    participant FHIR as FHIR API
    participant Validation as Validation Layer
    participant PG as PostgreSQL
    participant Mongo as MongoDB
    participant State as Patient State Engine
    participant Audit as Audit Ledger

    Source->>FHIR: Submit FHIR resources
    FHIR->>Validation: Validate supported semantics

    alt Valid resource
        Validation->>PG: Resolve identity / governance metadata
        Validation->>Mongo: Persist versioned FHIR document
        Validation->>Audit: Record ingestion outcome
        PG->>State: Identity / alias metadata
        Mongo->>State: Clinical documents
        State->>State: Recompute affected Patient 360 projection
    else Invalid resource
        Validation->>Audit: Record rejected ingestion
        Validation-->>FHIR: Structured validation errors
    end
```

## Imaging ingestion and retrieval

```mermaid
sequenceDiagram
    autonumber
    participant Modality as Imaging Modality
    participant DICOM as DICOMweb Gateway
    participant PACS as PACS/VNA
    participant Object as Object Storage
    participant FHIR as FHIR Layer
    participant P360 as Patient 360
    participant Viewer as DICOM Viewer

    Modality->>DICOM: DICOM C-STORE or STOW-RS
    DICOM->>PACS: Register study / series / instances
    PACS->>Object: Persist DICOM binary objects
    PACS->>FHIR: Associate ImagingStudy / report metadata
    FHIR->>P360: Add study to longitudinal record
    P360->>Viewer: Open authorised imaging study
    Viewer->>DICOM: QIDO-RS / WADO-RS
    DICOM->>PACS: Resolve study / series / instance
    PACS->>Object: Retrieve DICOM objects
    Object-->>PACS: Binary DICOM data
    PACS-->>Viewer: DICOMweb response
```

## Patient 360 derivation boundary

```mermaid
flowchart LR
    subgraph Clinical[FHIR clinical truth]
        PAT[Patient]
        ENC[Encounter]
        COND[Condition]
        OBS[Observation]
        MED[Medication]
        ALLERGY[AllergyIntolerance]
        PROC[Procedure]
        SR[ServiceRequest]
        DOC[DocumentReference]
        REPORT[DiagnosticReport]
        IMGSTUDY[ImagingStudy]
        PROV[Provenance]
    end

    subgraph Imaging[DICOM imaging truth]
        STUDY[DICOM Study]
        SERIES[DICOM Series]
        INSTANCE[DICOM Instances / Frames]
    end

    ENGINE[Deterministic Patient State Engine]

    subgraph Read[Patient 360 derived model]
        ID[Identity]
        ACTIVE[Active Clinical State]
        TIMELINE[Longitudinal Timeline]
        TRENDS[Laboratory Trends]
        IMAGING[Imaging Study References]
        PENDING[Pending Care]
        SOURCES[Source Traceability]
    end

    PAT --> ENGINE
    ENC --> ENGINE
    COND --> ENGINE
    OBS --> ENGINE
    MED --> ENGINE
    ALLERGY --> ENGINE
    PROC --> ENGINE
    SR --> ENGINE
    DOC --> ENGINE
    REPORT --> ENGINE
    IMGSTUDY --> ENGINE
    PROV --> ENGINE
    STUDY --> ENGINE

    ENGINE --> ID
    ENGINE --> ACTIVE
    ENGINE --> TIMELINE
    ENGINE --> TRENDS
    ENGINE --> IMAGING
    ENGINE --> PENDING
    ENGINE --> SOURCES

    SERIES --> STUDY
    INSTANCE --> SERIES
```

Patient 360 derives imaging references and summary metadata; the DICOM study/series/instance hierarchy remains authoritative in the PACS/VNA.

## Authentication, authorisation, consent and audit

```mermaid
flowchart TD
    USER[Clinician or Patient]
    AUTH[OIDC / OAuth2 Identity Provider]
    RBAC[Role / Scope Evaluation]
    CONSENT[Consent / Purpose Policy]
    API[Patient 360 API]
    DATA[(Patient 360 Projection)]
    FHIR[(FHIR Document Store)]
    DICOM[DICOMweb Gateway]
    VIEWER[DICOM Viewer]
    AUDIT[(Append-oriented Audit Log)]

    USER --> AUTH
    AUTH --> RBAC
    RBAC --> CONSENT
    CONSENT -->|Authorised request| API
    API --> DATA
    API -->|Clinical source drill-down| FHIR
    API -->|Authorised imaging context| VIEWER
    VIEWER --> DICOM
    API --> AUDIT
    VIEWER --> AUDIT
    CONSENT -->|Denied request| AUDIT
```

## Trust boundaries

```mermaid
flowchart LR
    subgraph External[External / simulated sources]
        CLINSRC[Clinical Source Systems]
        MODALITIES[Imaging Modalities]
    end

    subgraph Platform[SNS Patient 360 platform]
        FHIRAPI[FHIR API]
        DICOM[DICOMweb Gateway]
        PG[(PostgreSQL)]
        MONGO[(MongoDB)]
        PACS[(PACS / VNA)]
        OBJECT[(Object Storage)]
        STATE[Patient State Engine]
        REDIS[(Redis)]
        AUDIT[(Audit Store)]
    end

    subgraph Clients[Client boundary]
        CLINICIAN[Clinician Client / Viewer]
        PATIENT[Patient Client]
    end

    CLINSRC --> FHIRAPI
    MODALITIES --> DICOM
    FHIRAPI --> PG
    FHIRAPI --> MONGO
    DICOM --> PACS
    PACS --> OBJECT
    PG --> STATE
    MONGO --> STATE
    PACS --> STATE
    STATE --> REDIS
    STATE --> CLINICIAN
    STATE --> PATIENT
    CLINICIAN --> DICOM
    FHIRAPI --> AUDIT
    DICOM --> AUDIT
    CLINICIAN --> AUDIT
    PATIENT --> AUDIT
```

## Architecture-to-requirements relationship

The architecture is governed by [`requirements.md`](requirements.md). Diagnostic imaging requirements explicitly distinguish FHIR metadata from DICOM pixel storage and retrieval. Implementation PRs should reference the requirement IDs they satisfy and add verification at the appropriate level: unit, contract, integration, security or performance testing.
