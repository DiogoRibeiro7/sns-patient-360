# ADR 0004 — Use polyglot persistence

- Status: Accepted
- Date: 2026-09-01

## Context

SNS Patient 360 combines data with materially different shapes and access patterns:

- patient identity, source aliases, consent/audit metadata and ingestion state are strongly relational;
- FHIR resources are nested, versioned clinical documents whose native structure should be preserved;
- Patient 360 projections are derived and may benefit from low-latency disposable caching.

Using one relational database for all three concerns would force document-shaped FHIR resources into a relational storage model without a corresponding benefit.

## Decision

The reference architecture uses polyglot persistence:

1. **PostgreSQL** stores relational identity, source aliases, consent/audit metadata and ingestion coordination state.
2. **MongoDB** stores complete, versioned FHIR resource documents keyed by source system, resource type, resource id and version id.
3. **Redis** stores only disposable derived Patient 360 cache entries. Redis is never authoritative clinical storage.

Automated unit tests MAY replace external databases with deterministic in-memory/test doubles. Integration environments SHOULD exercise the real database technologies through Docker Compose.

## Consistency model

A single ACID transaction cannot span PostgreSQL and MongoDB without introducing distributed transaction machinery. The reference architecture therefore uses a recoverable, idempotent write protocol:

- deterministic identifiers and source-version keys;
- append/version-preserving document writes;
- relational ingestion state and audit records;
- safe replay after partial failure;
- reconciliation of incomplete ingestion operations.

The system MUST NOT report an ingestion operation as fully committed unless the required relational metadata and FHIR document writes have completed.

## Consequences

### Positive

- FHIR resources retain their native document structure.
- Relational constraints remain available where they are valuable.
- Patient 360 reads can later be cached without weakening the source-of-truth model.
- Each data technology has one explicit responsibility.

### Negative

- Operational complexity increases.
- Cross-database consistency must be explicit and testable.
- Backup, monitoring and recovery procedures must cover more than one persistent database.

## Rejected alternatives

### PostgreSQL only

Rejected as the default architecture because the complete FHIR resource payload is fundamentally document-shaped and evolves independently across resource types.

### MongoDB only

Rejected because patient identity aliases, consent/audit relationships and ingestion coordination benefit from relational constraints and transactional semantics.

### Redis as primary storage

Rejected because Patient 360 projections are rebuildable derived state and Redis must remain disposable.
