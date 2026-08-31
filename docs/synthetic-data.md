# Synthetic clinical ecosystem

## Purpose

The synthetic ecosystem implements `FR-060`, `FR-061`, `FR-062`, `NFR-070` and `NFR-071` without relying on real healthcare systems or patient data.

The current milestone provides one deterministic synthetic patient journey spanning four independently generated clinical source systems:

- primary care;
- hospital;
- laboratory;
- pharmacy.

Each source owns a different local patient identifier. The sources are correlated only through clearly synthetic master identifiers used by this reference implementation.

## Canonical synthetic journey

```mermaid
timeline
    title Synthetic Patient Journey
    2026-02-11 : Primary care consultation
               : Hypertension recorded
               : Ramipril 5 mg started
    2026-02-12 : Pharmacy dispenses Ramipril
    2026-03-03 : Laboratory HbA1c 7.4%
    2026-05-04 : Emergency encounter for chest pain
               : Troponin normal
    2026-06-02 : Cardiology referral created
    2026-07-18 : Cardiology follow-up
               : ECG normal sinus rhythm
    2026-08-23 : Laboratory HbA1c 6.8%
               : Creatinine 0.91 mg/dL
```

## Source independence

```mermaid
flowchart LR
    PATIENT[Synthetic person]

    PC[Primary Care\nUSF local patient ID]
    HOSP[Hospital\nHospital local patient ID]
    LAB[Laboratory\nLaboratory local patient ID]
    PHARM[Pharmacy\nPharmacy local patient ID]

    PATIENT -. synthetic correlation only .-> PC
    PATIENT -. synthetic correlation only .-> HOSP
    PATIENT -. synthetic correlation only .-> LAB
    PATIENT -. synthetic correlation only .-> PHARM

    PC --> PCFHIR[Primary-care FHIR-shaped bundle]
    HOSP --> HFHIR[Hospital FHIR-shaped bundle]
    LAB --> LFHIR[Laboratory FHIR-shaped bundle]
    PHARM --> PFHIR[Pharmacy FHIR-shaped bundle]
```

The source bundles are exported independently. Patient 360 assembly is deliberately not performed in this milestone; it belongs to the ingestion and identity-resolution milestones.

## Reproducibility

The default journey uses seed `360`. For a fixed seed, all patient identifiers, source records and timestamps are deterministic.

Generate source bundles with:

```bash
sns360-synthetic --seed 360 --output-dir synthetic/generated
```

The command writes:

```text
synthetic/generated/
  primary-care.json
  hospital.json
  laboratory.json
  pharmacy.json
```

Generated files are intended as disposable build artefacts. The source generator and its tests are the canonical definition of the synthetic journey.

## Safety boundary

All identifiers are synthetic and explicitly labelled as such. The generator does not query external healthcare services, and the default CI suite requires no external clinical dependency.
