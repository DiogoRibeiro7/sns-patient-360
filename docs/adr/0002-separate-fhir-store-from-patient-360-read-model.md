# ADR 0002 — Separate the FHIR store from the Patient 360 read model

- Status: Accepted
- Date: 2026-08-31

## Context

FHIR resources preserve clinical semantics and interoperability, but clinician-facing queries require a compact longitudinal representation of current state, history and pending care.

## Decision

Maintain the source FHIR representation separately from a derived Patient 360 read model. The read model may aggregate and index information for user-facing queries, but every derived clinical item must retain references to the source resources that justify it.

## Consequences

- User interfaces can query a purpose-built longitudinal model without weakening source fidelity.
- Derived state can be rebuilt from source records.
- Conflicts and historical versions can remain visible.
- Read-model logic becomes testable domain code rather than presentation-layer behaviour.