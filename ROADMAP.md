# Roadmap

## v0.1.0 — Longitudinal Patient 360 foundation

The first release proves that fragmented synthetic clinical records can be reconstructed into one auditable longitudinal patient view.

### Milestone 1 — Architecture and contracts
- Product scope and non-goals
- Canonical Patient 360 model
- HL7 FHIR resource subset
- Mermaid system, data-flow and trust-boundary diagrams
- Functional/non-functional requirements with stable IDs
- Provenance, audit and synthetic-data policies
- Security/threat model and ADRs

### Milestone 2 — Synthetic clinical ecosystem
- Primary-care source
- Hospital source
- Laboratory source
- Pharmacy source
- Reproducible synthetic patient identities and journeys

### Milestone 3 — FHIR ingestion and longitudinal store
- FHIR validation and source normalisation
- Patient identity resolution
- Provenance preservation
- PostgreSQL for relational identity, alias and ingestion metadata
- MongoDB for complete versioned FHIR resource documents
- Recoverable idempotent cross-database write protocol
- Redis reserved for non-authoritative Patient 360 projection caching

### Milestone 4 — Diagnostic imaging architecture
- FHIR `ImagingStudy`, `DiagnosticReport` and `Endpoint` scope
- DICOM/DICOMweb interoperability boundary
- PACS/VNA ownership of study/series/instance lifecycle
- QIDO-RS, WADO-RS and STOW-RS contracts
- S3-compatible bulk object storage behind the PACS/VNA
- Orthanc + MinIO local reference stack
- Imaging-specific functional/non-functional requirements
- Mermaid imaging, retrieval, security and trust-boundary diagrams

### Milestone 5 — Synthetic imaging integration
- Synthetic DICOM study generation
- CT/X-ray/ultrasound-style synthetic examples where practical
- STOW-RS ingestion into the reference PACS
- `ImagingStudy` metadata association
- Study/report linkage
- QIDO-RS discovery and WADO-RS retrieval tests
- Patient identity linkage across FHIR and DICOM planes

### Milestone 6 — Patient State Engine and Patient 360 API
- Patient summary
- Active problems
- Current medication
- Allergies
- Unified clinical timeline
- Laboratory trends
- Diagnostic imaging references
- Pending care items
- Rebuildable Redis projection cache where useful

### Milestone 7 — Clinician interface
- Longitudinal timeline
- Clinical-state summary
- Laboratory trends
- Imaging study list and report linkage
- Authorised DICOM viewer handoff
- Source drill-down and provenance

### Milestone 8 — Patient interface
- Results
- Appointments
- Referrals
- Medication
- Vaccinations
- Imaging reports/study metadata appropriate for patient access
- Consent and access history

### Later work
- Descriptive longitudinal analytics
- Care-pathway signals
- Source-grounded document summarisation
- Natural-language navigation over the clinical record
- Specialised imaging domains such as pathology/whole-slide imaging only after their standards/profile requirements are explicitly designed

AI-generated diagnosis, automated image interpretation and autonomous treatment recommendations are explicitly out of scope.

The authoritative baseline requirements live in [`docs/architecture/requirements.md`](docs/architecture/requirements.md), with imaging-specific requirements in [`docs/architecture/imaging-requirements.md`](docs/architecture/imaging-requirements.md).
