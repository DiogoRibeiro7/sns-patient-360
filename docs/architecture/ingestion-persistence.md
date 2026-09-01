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
    participant SQL as PostgreSQL Identity / Audit Store
    participant Mongo as MongoDB FHIR Document Store
    participant Ledger as Ingestion Event Ledger

    Source->>Validator: Submit collection Bundle
    Validator->>Validator: Validate resource shape, ids, source and synthetic markers

    alt Bundle invalid
        Validator->>Ledger: Append rejected event
        Validator-->>Source: Structured rejection
    else Bundle valid
        Validator->>Resolver: Source-local Patient + shared synthetic identifier
        Resolver->>SQL: Resolve/create canonical patient
        Resolver->>SQL: Attach source-local alias
        loop Each resource version
            Mongo->>Mongo: Check source × type × id × version
            alt Exact resource version already stored
                Mongo->>Mongo: Count duplicate
            else New resource version
                Mongo->>Mongo: Append complete FHIR document
            end
        end
        SQL->>Ledger: Mark ingestion committed
    end
```

## Polyglot persistence architecture

```mermaid
flowchart TB
    API[FHIR Ingestion Service]
    RESOLVE[Identity Resolver]
    STATE[Patient State Engine]
    READ[Patient 360 API]

    PG[(PostgreSQL)]
    MONGO[(MongoDB)]
    REDIS[(Redis)]

    API --> RESOLVE
    RESOLVE --> PG
    API --> MONGO

    PG --> STATE
    MONGO --> STATE
    STATE --> REDIS
    STATE --> READ
    REDIS --> READ

    PG -. identity, aliases, consent/audit, ingestion state .-> PG
    MONGO -. complete versioned FHIR documents .-> MONGO
    REDIS -. disposable derived projections only .-> REDIS
```

### PostgreSQL responsibility

PostgreSQL owns data with strong relational constraints:

- canonical patient identity;
- source-local patient aliases;
- consent and access-control metadata as introduced;
- ingestion coordination state;
- audit/ingestion ledger metadata.

### MongoDB responsibility

MongoDB owns complete clinical source documents:

- FHIR payloads are stored without flattening their nested structure;
- source-version identity is `(source, resourceType, id, versionId)`;
- exact replay is idempotent;
- a different payload under the same source-version key is rejected;
- new source versions are appended rather than overwriting history;
- documents remain queryable by canonical patient id and resource type.

### Redis responsibility

Redis is reserved for rebuildable Patient 360 projections and cache entries. It is explicitly non-authoritative: deletion or total Redis loss must not destroy clinical truth, because projections can be reconstructed from PostgreSQL plus MongoDB.

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
    PG[(PostgreSQL aliases)]
    MONGO[(MongoDB FHIR documents)]

    PC --> ID
    H --> ID
    L --> ID
    P --> ID
    ID --> RESOLVE
    RESOLVE --> CANON
    CANON --> PG
    CANON --> MONGO
```

The current resolver intentionally uses the explicit shared synthetic identifier. Probabilistic or demographic record linkage is out of scope and must not be introduced silently.

## Cross-database consistency

PostgreSQL and MongoDB do not share one implicit ACID transaction boundary. The architecture therefore uses a recoverable idempotent protocol rather than pretending distributed atomicity exists.

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Validated: validation succeeds
    Received --> Rejected: validation fails
    Validated --> IdentityCommitted: canonical identity / alias committed
    IdentityCommitted --> DocumentsCommitted: FHIR document versions written
    DocumentsCommitted --> Committed: ingestion ledger finalised

    IdentityCommitted --> RecoveryRequired: document write interrupted
    RecoveryRequired --> DocumentsCommitted: safe replay / reconciliation
    Rejected --> [*]
    Committed --> [*]
```

Deterministic source-version keys and idempotent replay make partial operations recoverable. The application must not expose an ingestion operation as fully committed until both the relational metadata and required MongoDB document writes have succeeded.

## Local development

`docker-compose.yml` provides:

- PostgreSQL for relational state;
- MongoDB for FHIR documents;
- Redis for disposable projection caching.

Unit tests may use isolated in-memory/test doubles so the default CI suite remains independent of external healthcare systems. Database integration tests should use the real services in dedicated integration workflows.

## Next boundary

The Patient State Engine will consume PostgreSQL identity metadata plus MongoDB FHIR documents and produce rebuildable Patient 360 projections. Redis may accelerate those reads but must never become the only copy of clinically significant state.
