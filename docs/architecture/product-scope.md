# Product scope

## Problem

A clinician should be able to understand the current state and longitudinal history of a patient without navigating multiple disconnected clinical systems.

SNS Patient 360 is a reference platform that reconstructs a unified patient-centred view from interoperable clinical records while preserving provenance, consent and auditability.

## MVP questions

The first usable release must answer:

1. Who is this patient?
2. What are the active clinical problems?
3. What medication, allergies and relevant treatments exist?
4. What happened to the patient over time?
5. What is pending or requires attention?

## In scope

- Longitudinal patient record reconstruction
- HL7 FHIR interoperability contracts
- Synthetic primary-care, hospital, laboratory and pharmacy systems
- Deterministic clinical-state aggregation
- Clinical timeline generation
- Provenance and source traceability
- Consent representation
- Auditable record access
- Clinician and patient-facing read models

## Non-goals for v0.1

- Real SNS or SPMS connectivity
- Real patient data
- Clinical diagnosis by AI
- Autonomous treatment recommendations
- Billing or reimbursement
- Hospital administration
- Replacement of source clinical systems
- Production deployment into healthcare infrastructure

## Safety boundary

All repository examples, fixtures and demonstrations must use synthetic data. No production secrets, credentials, identifiers or patient records may be committed.

## Positioning

This repository is an independent technical reference implementation. It is not an official SNS, SPMS or Portuguese government product.