# ADR 0001 — Use HL7 FHIR as the interoperability contract

- Status: Accepted
- Date: 2026-08-31

## Context

The platform must integrate records originating from heterogeneous clinical systems without binding the application to one vendor-specific schema.

## Decision

Use HL7 FHIR resources as the canonical interoperability boundary. Source adapters may transform external representations into FHIR, but the Patient 360 read model must be derived from validated FHIR resources rather than directly from vendor schemas.

## Consequences

- Source systems remain decoupled from the application read model.
- Provenance can reference stable clinical resources.
- The system can evolve toward Portuguese and European implementation profiles without redesigning its core boundary.
- FHIR conformance and terminology validation become explicit engineering responsibilities.