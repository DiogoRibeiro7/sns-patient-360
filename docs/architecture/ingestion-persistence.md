# FHIR ingestion and canonical longitudinal persistence

## Scope

This milestone implements the boundary between independent source bundles and the canonical clinical store. It does not yet derive the Patient 360 read model.

Implements: `FR-001`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `FR-014`, `FR-020`, `NFR-020`, `NFR-021`, `NFR-022`, `NFR-023`, `NFR-042`.

## Ingestion flow

```mermaid
sequenceDiagram
    autonumber
    participant Source as Source FHIR Bundle
    participant Validator as FHIR Validator
    participant Resolver as Identity Resolver
    participant Store as Canonical Clinical Store
    participant Ledger as Ingestion Event Ledger

    Source->>Validator: Submit collection Bundle
    Validator->>Validator: Check resource type, ids, source, synthetic tag and subject references

    alt Bundle invalid
        Validator->>Ledger: Append rejected event
        Validator-->>Source: Structured rejection
    else Bundle valid
        Validator->>Resolver: Source-local Patient + shared synthetic identifier
        Resolver->>Store: Resolve/create canonical patient
        Resolver->>Store: Attach source-local alias
        loop Each resource version
            Store->>Store: Check source × type × id × version
            alt Exact resource version already stored
                Store->>Store: Count duplicate
            else New resource version
                Store->>Store: Append canonical source resource
            end
        end
        Store->>Ledger: Append accepted event
    end
```

## Identity-resolution boundary

```mermaid
flowchart LR
    PC[Primary Care Patient<br/>USF-*]
    H[Hospital Patient<br/>HOSP-*]
    L[Laboratory Patient<br/>LAB-*]
    P[Pharmacy Patient<br/>PHARM-*]

    ID[Shared synthetic identifier]
    RESOLVE[Deterministic Identity Resolver]
    CANON[Canonical Patient ID]

    PC --> ID
    H --> ID
    L --> ID
    P --> ID
    ID --> RESOLVE
    RESOLVE --> CANON

    CANON --> A1[Alias: primary-care → USF-*]
    CANON --> A2[Alias: hospital → HOSP-*]
    CANON --> A3[Alias: laboratory → LAB-*]
    CANON --> A4[Alias: pharmacy → PHARM-*]
```

The current resolver intentionally uses the explicit shared synthetic identifier. Probabilistic or demographic record linkage is out of scope for this milestone and must not be introduced silently.

## Persistence model

```mermaid
erDiagram
    CANONICAL_PATIENT ||--o{ SOURCE_ALIAS : has
    CANONICAL_PATIENT ||--o{ CLINICAL_RESOURCE : owns

    CANONICAL_PATIENT {
        string canonical_patient_id PK
        string synthetic_national_health_id UK
    }

    SOURCE_ALIAS {
        string source_system PK
        string source_patient_id PK
        string canonical_patient_id FK
    }

    CLINICAL_RESOURCE {
        string source_system PK
        string resource_type PK
        string resource_id PK
        string version_id PK
        string canonical_patient_id FK
        json payload
        datetime ingested_at
    }

    INGESTION_EVENT {
        string event_id PK
        string source_system
        string outcome
        string detail
        datetime occurred_at
    }
```

The source-version key is:

\[
(\text{source},\ \text{resourceType},\ \text{id},\ \text{versionId})
\]

An exact replay is idempotent. A new version is appended. A different payload presented under an already stored source-version key is rejected rather than silently overwriting the canonical record.

## Database portability

The persistence layer is implemented with SQLAlchemy. Automated tests use SQLite so CI has no external clinical or database dependency. The schema and transaction boundary are intentionally database-portable; PostgreSQL remains the target persistent database for the reference deployment architecture.

## Next boundary

The next milestone consumes the canonical clinical store and derives the Patient 360 read model:

```mermaid
flowchart LR
    STORE[(Canonical FHIR Store)]
    ENGINE[Patient State Engine]
    READ[(Patient 360 Read Model)]

    STORE --> ENGINE
    ENGINE --> READ
```
