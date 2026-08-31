# Roadmap

## v0.1.0 — Longitudinal Patient 360 foundation

The first release proves that fragmented synthetic clinical records can be reconstructed into one auditable longitudinal patient view.

### Milestone 1 — Architecture and contracts
- Product scope and non-goals
- Canonical Patient 360 model
- Initial HL7 FHIR resource subset
- Provenance and audit requirements
- Synthetic-data-only policy
- Security and threat model
- Architecture decision records

### Milestone 2 — Synthetic clinical ecosystem
- Primary-care source
- Hospital source
- Laboratory source
- Pharmacy source
- Reproducible synthetic patient identities and journeys

### Milestone 3 — FHIR ingestion and longitudinal store
- FHIR validation
- Source normalization
- Patient identity resolution
- Provenance preservation
- PostgreSQL persistence

### Milestone 4 — Patient 360 API
- Patient summary
- Active problems
- Current medication
- Allergies
- Unified clinical timeline
- Pending care items

### Milestone 5 — Clinician interface
- Longitudinal timeline
- Clinical-state summary
- Laboratory trends
- Source drill-down

### Milestone 6 — Patient interface
- Results
- Appointments
- Referrals
- Medication
- Vaccinations
- Consent and access history

### Later work
- Descriptive longitudinal analytics
- Care-pathway signals
- Source-grounded document summarisation
- Natural-language navigation over the clinical record

AI-generated diagnosis and autonomous treatment recommendations are explicitly out of scope.