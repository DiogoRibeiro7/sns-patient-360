# Initial HL7 FHIR scope

FHIR is the interoperability contract. The Patient 360 application model is a separate read model derived from validated FHIR resources.

## Initial resources

| Resource | Purpose in Patient 360 |
| --- | --- |
| `Patient` | Patient identity and demographics |
| `Practitioner` | Clinical professional identity |
| `Organization` | Source and care-provider organization |
| `Encounter` | Consultations, admissions and emergency episodes |
| `Condition` | Diagnoses and active clinical problems |
| `Observation` | Laboratory values, vital signs and measured clinical facts |
| `DiagnosticReport` | Laboratory and diagnostic report containers |
| `MedicationRequest` | Prescribed medication |
| `AllergyIntolerance` | Allergies and intolerances |
| `Immunization` | Vaccination history |
| `Procedure` | Clinical and surgical procedures |
| `CarePlan` | Planned longitudinal care |
| `Appointment` | Scheduled care interactions |
| `ServiceRequest` | Referrals, tests and requested services |
| `DocumentReference` | Clinical documents and reports |
| `Consent` | Patient consent and sharing policy representation |
| `Provenance` | Origin and transformation traceability |
| `AuditEvent` | Access and security audit events |

## Contract principles

1. Source payloads are validated before they enter the longitudinal store.
2. Source-specific extensions must not silently alter standard FHIR semantics.
3. Derived Patient 360 fields must retain links to their originating resources.
4. Conflicting source records are preserved and surfaced rather than silently overwritten.
5. Clinical state is time-dependent; the system must distinguish current state from historical facts.
6. Terminology bindings and Portuguese implementation profiles will be introduced explicitly rather than guessed.

## Patient 360 read model

```text
Patient360
├── identity
├── clinical_state
│   ├── active_conditions
│   ├── active_medications
│   ├── allergies
│   └── pending_care
├── timeline
├── laboratory_trends
├── procedures
├── referrals
├── appointments
├── documents
└── provenance
```

The read model is designed for user-facing queries. It is not a replacement for the underlying FHIR resources.