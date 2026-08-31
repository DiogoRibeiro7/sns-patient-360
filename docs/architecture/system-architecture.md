# System architecture

## Purpose

SNS Patient 360 reconstructs a unified longitudinal patient view from fragmented clinical source systems while preserving the clinical meaning, provenance, consent context and auditability of the source records.

The platform does not replace source clinical systems. HL7 FHIR is the interoperability boundary, while Patient 360 is a derived read model optimised for clinician and patient-facing queries.

All architecture diagrams in this repository are expressed as Mermaid inside versioned Markdown documents.

## Architectural principles

1. **FHIR remains the source and interchange truth.** Patient 360 does not redefine the semantics of source clinical resources.
2. **Derived state is traceable.** Every derived Patient 360 item must link to the FHIR resources that support it.
3. **Conflicts are preserved.** Conflicting or superseded clinical facts must not be silently overwritten.
4. **Clinical state is temporal.** Current state and historical facts are distinct concepts.
5. **Access is auditable.** Reads and transformations of clinical information must be attributable.
6. **Synthetic data only.** The reference implementation must not contain real patient data.
7. **AI is not part of the clinical truth layer.** Diagnosis and autonomous treatment recommendations are out of scope.

## System context

```mermaid
flowchart LR
    PC[Primary Care System]
    HOSP[Hospital System]
    LAB[Laboratory System]
    PHARM[Pharmacy System]

    P360[SNS Patient 360]
    CLINICIAN[Clinician]
    PATIENT[Patient]
    AUDITOR[Auditor / Security Reviewer]

    PC -->|FHIR resources| P360
    HOSP -->|FHIR resources| P360
    LAB -->|FHIR resources| P360
    PHARM -->|FHIR resources| P360

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
    end

    subgraph Interop[Interoperability boundary]
        API[FHIR API]
        VALIDATE[Validation and Normalisation]
    end

    subgraph Clinical[Clinical data layer]
        FHIRSTORE[(FHIR Clinical Store)]
        PROV[Provenance Service]
        AUDIT[Audit Service]
    end

    subgraph ReadModel[Patient 360 layer]
        STATE[Patient State Engine]
        P360STORE[(Patient 360 Read Model)]
    end

    subgraph Experience[Experience layer]
        CLINAPI[Patient 360 API]
        CLINWEB[Clinician Web]
        PATWEB[Patient Web]
    end

    Sources -->|FHIR bundles / resources| API
    API --> VALIDATE
    VALIDATE -->|Validated canonical resources| FHIRSTORE
    VALIDATE -->|Source and ingestion metadata| PROV
    VALIDATE -->|Ingestion audit events| AUDIT

    FHIRSTORE --> STATE
    PROV --> STATE
    STATE --> P360STORE
    STATE -->|Derivation records| PROV

    P360STORE --> CLINAPI
    CLINAPI --> CLINWEB
    CLINAPI --> PATWEB
    CLINAPI -->|Access events| AUDIT
```

## Ingestion and derivation sequence

```mermaid
sequenceDiagram
    autonumber
    participant Source as Source System
    participant API as FHIR API
    participant Validation as Validation Layer
    participant Store as FHIR Store
    participant Provenance as Provenance Service
    participant State as Patient State Engine
    participant ReadModel as Patient 360 Read Model
    participant Audit as Audit Service

    Source->>API: Submit FHIR resources
    API->>Validation: Validate structure and supported semantics

    alt Valid resource
        Validation->>Store: Persist canonical source resource
        Validation->>Provenance: Record source and ingestion provenance
        Validation->>Audit: Record successful ingestion
        Store->>State: Make validated resource available
        Provenance->>State: Provide provenance links
        State->>ReadModel: Recompute affected patient state
        State->>Provenance: Record derivation provenance
    else Invalid resource
        Validation->>Audit: Record rejected ingestion
        Validation-->>API: Return validation errors
        API-->>Source: Reject resource
    end
```

## Patient 360 derivation boundary

```mermaid
flowchart LR
    subgraph FHIR[FHIR clinical truth]
        PAT[Patient]
        ENC[Encounter]
        COND[Condition]
        OBS[Observation]
        MED[MedicationRequest]
        ALLERGY[AllergyIntolerance]
        PROC[Procedure]
        SR[ServiceRequest]
        DOC[DocumentReference]
        PROV[Provenance]
    end

    ENGINE[Deterministic Patient State Engine]

    subgraph P360[Patient 360 derived read model]
        ID[Identity]
        ACTIVE[Active Clinical State]
        TIMELINE[Longitudinal Timeline]
        TRENDS[Laboratory Trends]
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
    PROV --> ENGINE

    ENGINE --> ID
    ENGINE --> ACTIVE
    ENGINE --> TIMELINE
    ENGINE --> TRENDS
    ENGINE --> PENDING
    ENGINE --> SOURCES
```

## Authentication, authorisation, consent and audit

```mermaid
flowchart TD
    USER[Clinician or Patient]
    AUTH[OIDC / OAuth2 Identity Provider]
    RBAC[Role and Scope Evaluation]
    CONSENT[Consent Policy Evaluation]
    API[Patient 360 API]
    DATA[(Patient 360 Read Model)]
    FHIR[(FHIR Clinical Store)]
    AUDIT[(Append-oriented Audit Log)]

    USER --> AUTH
    AUTH --> RBAC
    RBAC --> CONSENT
    CONSENT -->|Authorised request| API
    API --> DATA
    API -->|Source drill-down when authorised| FHIR
    API -->|Actor, purpose, resource, outcome, timestamp| AUDIT
    CONSENT -->|Denied request| AUDIT
```

## Trust boundaries

```mermaid
flowchart LR
    subgraph External[External / simulated source boundary]
        SOURCES[Clinical Source Systems]
    end

    subgraph Platform[SNS Patient 360 platform boundary]
        FHIRAPI[FHIR API]
        VALIDATION[Validation]
        STORE[(Clinical Store)]
        STATE[Patient State Engine]
        P360[(Patient 360 Read Model)]
        AUDIT[(Audit Store)]
    end

    subgraph Clients[Client boundary]
        CLINICIAN[Clinician Client]
        PATIENT[Patient Client]
    end

    SOURCES -->|Validated authenticated channel| FHIRAPI
    FHIRAPI --> VALIDATION
    VALIDATION --> STORE
    STORE --> STATE
    STATE --> P360
    VALIDATION --> AUDIT
    P360 --> CLINICIAN
    P360 --> PATIENT
    CLINICIAN --> AUDIT
    PATIENT --> AUDIT
```

## Architecture-to-requirements relationship

The architecture is governed by the requirements in [`requirements.md`](requirements.md). Functional requirements define observable platform behaviour. Non-functional requirements define the quality, safety, interoperability and operational constraints under which that behaviour must be delivered.

Implementation PRs should reference the requirement IDs they satisfy and add verification at the appropriate level: unit, contract, integration, security or performance testing.
