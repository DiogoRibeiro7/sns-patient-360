# Security and threat model

## Security objectives

SNS Patient 360 must be designed around confidentiality, integrity, availability, traceability and least privilege. The repository is a reference implementation using synthetic data only, but its architecture should not teach unsafe healthcare patterns.

## Assets

- Patient identity data
- Clinical records
- Consent state
- Authentication and authorization context
- Provenance metadata
- Audit history
- Service credentials and secrets

## Trust boundaries

```text
Synthetic source systems
        │
        ▼
FHIR ingestion boundary
        │
        ▼
Validated clinical store
        │
        ├── Patient-state service
        ├── Audit service
        └── API
               │
               ├── Clinician application
               └── Patient application
```

Each boundary requires authenticated service identity and explicit authorization.

## Principal threats

### Unauthorized record access
A user or service obtains information outside its permitted patient, role or purpose scope.

Controls:
- OAuth2/OIDC authentication
- Role and scope-based authorization
- Least privilege
- Purpose-of-use checks where supported
- Deny-by-default policies
- Access audit events

### Broken patient identity resolution
Records from different people are incorrectly joined.

Controls:
- Explicit identity-resolution rules
- Confidence and conflict representation
- No silent fuzzy merge in the clinical path
- Test fixtures for collisions and ambiguous identifiers

### Clinical record tampering
A stored or in-transit record is modified without detection.

Controls:
- TLS in transit
- Database access controls
- Immutable provenance references
- Append-oriented audit trail
- Integrity checks for imported artifacts where appropriate

### Provenance loss
Derived information cannot be traced to source records.

Controls:
- Source identifiers retained at ingestion
- Derived Patient 360 items contain source references
- Transformation metadata recorded
- No derived clinical claim without traceable evidence

### Over-privileged service accounts
One compromised service obtains broad access to the platform.

Controls:
- Separate service identities
- Minimal database privileges
- Secret rotation
- No shared production credentials

### Audit-log manipulation
An attacker deletes or changes evidence of record access.

Controls:
- Append-oriented audit storage
- Restricted write path
- Separate audit service boundary
- Operational monitoring in deployment environments

### Synthetic-data boundary failure
Real patient information is accidentally committed to the repository.

Controls:
- Synthetic-data-only contribution policy
- Fixture-generation scripts instead of copied datasets
- Secret and identifier scanning in CI
- Explicit review checklist

## Privacy principles

- Data minimisation
- Purpose limitation
- Least privilege
- Explicit retention policies in deployment profiles
- Patient-visible access history as a product capability
- Consent represented as data, not hidden application state

## Out of scope

This threat model is not a certification, DPIA, penetration test or claim of GDPR/EHDS compliance. Production healthcare deployment would require formal legal, organizational and security assessment.