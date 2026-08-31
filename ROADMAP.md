# Roadmap

## v0.1.0 — Longitudinal Patient 360 foundation

The first release proves that fragmented synthetic clinical records can be reconstructed into one auditable longitudinal patient view.

### Milestone 1 — Architecture and contracts
- Product scope and non-goals
- Canonical Patient 360 model
- Initial HL7 FHIR resource subset
- Mermaid system, data-flow and trust-boundary diagrams
- Functional requirements with stable `FR-*` identifiers
- Non-functional requirements with stable `NFR-*` identifiers
- Acceptance criteria and v0.1 requirement gate
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
- Implements primarily: FR-001, FR-060, FR-061, FR-062, NFR-070, NFR-071

### Milestone 3 — FHIR ingestion and longitudinal store
- FHIR validation
- Source normalization
- Patient identity resolution
- Provenance preservation
- PostgreSQL persistence
- Implements primarily: FR-010–FR-014, FR-020, NFR-010–NFR-023

### Milestone 4 — Patient 360 API
- Patient summary
- Active problems
- Current medication
- Allergies
- Unified clinical timeline
- Pending care items
- Implements primarily: FR-002–FR-006, FR-021, FR-040–FR-042

### Milestone 5 — Clinician interface
- Longitudinal timeline
- Clinical-state summary
- Laboratory trends
- Source drill-down
- Implements primarily: FR-040–FR-042, NFR-080–NFR-082

### Milestone 6 — Patient interface
- Results
- Appointments
- Referrals
- Medication
- Vaccinations
- Consent and access history
- Implements primarily: FR-034, FR-050–FR-052, NFR-080–NFR-082

### Later work
- Descriptive longitudinal analytics
- Care-pathway signals
- Source-grounded document summarisation
- Natural-language navigation over the clinical record

AI-generated diagnosis and autonomous treatment recommendations are explicitly out of scope.

The authoritative functional and non-functional requirement definitions live in [`docs/architecture/requirements.md`](docs/architecture/requirements.md).