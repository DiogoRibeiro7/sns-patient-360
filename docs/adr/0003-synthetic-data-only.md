# ADR 0003 — Keep the repository synthetic-data-only

- Status: Accepted
- Date: 2026-08-31

## Context

A public or collaborative healthcare reference implementation must not depend on access to real patient records in order to demonstrate architecture or behaviour.

## Decision

All committed clinical records, fixtures, screenshots and examples must be generated or explicitly synthetic. No real patient data is allowed in the repository.

## Consequences

- Reproducible fixtures become a first-class project component.
- Development and CI can run without privileged datasets.
- Demonstrations are safer to share.
- The repository must include checks and review practices that reduce the risk of accidental sensitive-data commits.