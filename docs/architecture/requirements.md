# Functional and non-functional requirements

## Purpose

This document defines the baseline requirements for SNS Patient 360. Requirement identifiers are stable references for architecture decisions, implementation pull requests, tests and future validation evidence.

The baseline describes a synthetic-data reference implementation. It does not assert regulatory certification, production readiness or connectivity to live SNS infrastructure.

## Requirement levels

- **MUST**: required for the stated milestone or release.
- **SHOULD**: expected unless a documented architecture decision justifies otherwise.
- **MAY**: optional capability.

# Functional requirements

## Patient identity and record assembly

### FR-001 — Unified patient identity
The system MUST maintain a canonical Patient 360 identity that can reference records originating from multiple source systems.

**Acceptance criteria**
- A synthetic patient represented in at least four source systems is reconstructed as one Patient 360 record.
- Source identifiers remain available for traceability.
- Identity resolution does not delete or rewrite source identifiers.

### FR-002 — Longitudinal patient record
The system MUST assemble validated clinical resources into a chronological patient record.

**Acceptance criteria**
- Encounters, observations, medication events and other supported resources can be ordered using clinically appropriate timestamps.
- The timeline distinguishes event time from ingestion time when both are available.
- Each timeline item retains source provenance.

### FR-003 — Current clinical state
The system MUST derive a current Patient 360 clinical state from the underlying source resources.

The initial state MUST include:
- active conditions;
- current medication;
- allergies and intolerances;
- pending care items.

**Acceptance criteria**
- Derived state is deterministic for a fixed set of source resources.
- Each derived item links to at least one supporting FHIR resource.
- Historical and inactive facts remain retrievable without being presented as current.

### FR-004 — Clinical timeline filtering
The system MUST allow the longitudinal timeline to be filtered by supported clinical categories.

Initial categories MUST include:
- encounters;
- laboratory results;
- medication;
- procedures;
- referrals and service requests;
- documents.

### FR-005 — Laboratory trends
The system MUST expose repeatable quantitative observations as longitudinal series when the observations are semantically comparable.

**Acceptance criteria**
- Each point retains timestamp, value, unit and provenance.
- Values with incompatible units or semantics are not silently merged into one series.

### FR-006 — Pending care
The system MUST surface supported unresolved care activities such as open service requests and future appointments.

**Acceptance criteria**
- Completed or cancelled items are not presented as pending.
- Source status and timestamp remain traceable.

## FHIR ingestion

### FR-010 — Supported FHIR ingestion
The system MUST ingest the supported FHIR resource types defined in `docs/data-model/fhir-scope.md`.

### FR-011 — Validation before persistence
FHIR resources MUST be validated before entering the canonical clinical store.

**Acceptance criteria**
- Invalid resources are rejected with structured validation errors.
- Rejected resources do not mutate the accepted clinical state.
- Rejections produce an audit event.

### FR-012 — Idempotent ingestion
Repeated ingestion of the same source resource version MUST NOT create duplicate clinical facts.

### FR-013 — Resource version preservation
When a source resource changes, the system MUST preserve enough version information to reconstruct how derived Patient 360 state changed over time.

### FR-014 — Conflict preservation
The system MUST preserve conflicting source assertions rather than resolving them through silent overwrite.

**Acceptance criteria**
- Conflicting records remain independently traceable.
- Any later conflict-resolution policy must be explicit and auditable.

## Provenance and audit

### FR-020 — Source provenance
Every accepted clinical resource MUST retain provenance sufficient to identify its source system and ingestion context.

### FR-021 — Derivation provenance
Every derived Patient 360 clinical item MUST retain links to the source resources used to derive it.

### FR-022 — Access audit
Access to patient clinical information MUST generate an audit record.

The audit record SHOULD include:
- actor;
- role;
- purpose;
- patient or resource scope;
- timestamp;
- action;
- outcome.

### FR-023 — Failed-access audit
Denied access attempts MUST be auditable.

## Authentication, authorisation and consent

### FR-030 — Authentication boundary
Protected Patient 360 endpoints MUST require authenticated identity.

### FR-031 — Role-based authorisation
The system MUST support authorisation decisions based on user role and requested scope.

### FR-032 — Consent representation
The system MUST be able to represent patient consent or sharing constraints using the supported clinical data model.

### FR-033 — Consent-aware access decision
Where a consent policy applies, access MUST be evaluated against that policy before protected clinical information is returned.

### FR-034 — Patient access history
The patient-facing model SHOULD expose an understandable history of accesses to the patient's record where the underlying audit events permit it.

## Clinician-facing capabilities

### FR-040 — Patient summary
The clinician-facing API MUST expose a compact Patient 360 summary including identity, active problems, medication, allergies, recent events and pending care.

### FR-041 — Source drill-down
A clinician with appropriate authorisation MUST be able to navigate from a derived Patient 360 item to its supporting source record or records.

### FR-042 — Recent clinical events
The clinician-facing API MUST expose recent clinical events in reverse chronological order by default.

## Patient-facing capabilities

### FR-050 — Patient health view
The patient-facing model SHOULD expose the patient's supported health information in a less clinically dense representation than the clinician view.

### FR-051 — Patient appointments and referrals
The patient-facing model SHOULD expose supported appointments, referrals and service requests with their current status.

### FR-052 — Patient medication and vaccination history
The patient-facing model SHOULD expose supported medication and immunisation records.

## Synthetic clinical ecosystem

### FR-060 — Synthetic-only fixtures
All committed patient-level data MUST be synthetic.

### FR-061 — Reproducible synthetic journey
The repository MUST provide at least one deterministic synthetic patient journey spanning primary care, hospital, laboratory and pharmacy systems.

### FR-062 — Source independence
Each synthetic source system MUST generate or expose records independently before those records are assembled into Patient 360.

# Non-functional requirements

## Security and privacy

### NFR-001 — No real patient data
No real patient health information, production credentials or production identifiers MAY be committed to the repository or required for automated tests.

### NFR-002 — Least privilege
Authorisation design MUST follow least-privilege principles. A user or service should receive only the permissions necessary for its role and operation.

### NFR-003 — Encryption boundaries
Production-oriented architecture MUST assume encryption in transit and at rest for protected clinical information. Local reference implementations MAY use development certificates or local-only infrastructure, but MUST document the difference.

### NFR-004 — Secret management
Secrets MUST NOT be committed to source control. Runtime credentials MUST be supplied through environment or secret-management mechanisms.

### NFR-005 — Audit integrity
Audit records MUST be append-oriented from the application perspective and MUST NOT be silently rewritten by ordinary application workflows.

### NFR-006 — Data minimisation
APIs and views SHOULD return only data required for the requested use case and authorised scope.

## Interoperability and semantic integrity

### NFR-010 — FHIR boundary
HL7 FHIR MUST remain the canonical interoperability contract for supported clinical exchange.

### NFR-011 — No silent semantic reinterpretation
Source-specific mappings, extensions or terminology conversions MUST NOT silently alter the meaning of clinical data.

### NFR-012 — Units and terminology
Quantitative clinical observations MUST retain units. Terminology mappings MUST be explicit and versionable when introduced.

### NFR-013 — Provenance completeness
A derived Patient 360 value MUST NOT be presented as source-grounded unless its supporting source resource identifiers are available.

## Reliability and data integrity

### NFR-020 — Deterministic derivation
For identical validated inputs and configuration, the Patient State Engine MUST produce identical derived state.

### NFR-021 — Transactional consistency
Persistence operations that update accepted clinical resources and their required metadata MUST avoid partial committed states.

### NFR-022 — Failure isolation
Invalid input from one source MUST NOT corrupt the accepted records originating from other sources.

### NFR-023 — Recoverability
The architecture SHOULD support rebuilding the Patient 360 read model from canonical source resources and provenance without manual reconstruction.

## Performance targets for the reference implementation

These are development targets, not production SNS service-level objectives.

### NFR-030 — Patient summary latency
For the v0.1 synthetic reference dataset, the local Patient 360 summary API SHOULD have a p95 server-side response time below 500 ms under single-user test conditions after warm-up.

### NFR-031 — Timeline latency
For the v0.1 synthetic reference dataset, the first page of the local timeline API SHOULD have a p95 server-side response time below 750 ms under single-user test conditions after warm-up.

### NFR-032 — Ingestion throughput
The reference implementation SHOULD be able to ingest at least 100 valid synthetic FHIR resources per minute on the documented development environment.

## Availability and resilience

### NFR-040 — Graceful dependency failure
A temporary failure in one external or simulated source MUST NOT make already persisted Patient 360 data unreadable.

### NFR-041 — Health checks
Runnable services MUST expose health or readiness information suitable for local orchestration and automated testing.

### NFR-042 — Safe retries
Operations documented as retryable MUST be idempotent or otherwise protected against duplicate clinical effects.

## Observability

### NFR-050 — Structured logging
Services SHOULD emit structured logs with correlation identifiers for cross-service operations.

### NFR-051 — No PHI in routine logs
Application logs MUST be designed to avoid unnecessary patient-level clinical payloads.

### NFR-052 — Traceable ingestion
An accepted or rejected ingestion request SHOULD be traceable across API, validation, persistence and audit components using a correlation identifier.

## Maintainability and software quality

### NFR-060 — Typed Python
Python implementation code MUST use type annotations and pass the repository's strict type-checking policy for covered modules.

### NFR-061 — Automated quality gates
The repository MUST maintain automated linting, type checking and tests in CI as executable code is introduced.

### NFR-062 — Architecture decision records
Material cross-cutting architectural decisions MUST be documented as ADRs.

### NFR-063 — Mermaid architecture diagrams
Architecture and process diagrams in versioned project documentation MUST use Mermaid rather than manually maintained ASCII diagrams or binary-only diagram sources.

### NFR-064 — Documentation-code alignment
When a change materially modifies architecture, supported FHIR scope or a requirement contract, the corresponding documentation MUST be updated in the same pull request.

## Testability and reproducibility

### NFR-070 — Deterministic test data
Synthetic fixtures used for contract and integration testing MUST be reproducible from fixed seeds or deterministic source definitions where randomness is involved.

### NFR-071 — No external clinical dependency in CI
The default CI suite MUST NOT depend on real healthcare systems or external patient data.

### NFR-072 — Requirement traceability
Implementation pull requests SHOULD reference applicable `FR-*` and `NFR-*` identifiers, and requirements with executable acceptance criteria SHOULD acquire automated verification as the relevant capability is implemented.

## Accessibility and usability

### NFR-080 — Accessibility target
Patient and clinician web interfaces SHOULD target WCAG 2.2 AA as they are introduced.

### NFR-081 — Clinical provenance visibility
Clinically significant derived information MUST provide a usable path to its provenance without requiring database-level access.

### NFR-082 — Clear state distinction
User interfaces MUST distinguish current, historical, pending, cancelled and conflicting information when those states are material to interpretation.

## Portability and local operation

### NFR-090 — Containerised local environment
Runnable backend dependencies SHOULD be reproducible using Docker Compose for local development.

### NFR-091 — No Kubernetes requirement for v0.1
The v0.1 reference implementation MUST NOT require Kubernetes to run locally.

### NFR-092 — Configuration separation
Environment-specific configuration MUST be separated from application code.

# v0.1 requirement gate

The following requirements form the minimum release gate for the first demonstrable longitudinal Patient 360 foundation:

- FR-001, FR-002, FR-003;
- FR-010, FR-011, FR-012, FR-014;
- FR-020, FR-021;
- FR-060, FR-061, FR-062;
- NFR-001, NFR-010, NFR-013;
- NFR-020, NFR-023;
- NFR-060, NFR-061, NFR-063;
- NFR-070, NFR-071.

# Traceability convention

Future implementation and test documentation should cite requirement IDs directly, for example:

```text
Implements: FR-011, FR-012, FR-020
Verifies: NFR-020, NFR-070
```

This keeps product intent, architecture, implementation and verification connected without turning the requirements document into an implementation log.
