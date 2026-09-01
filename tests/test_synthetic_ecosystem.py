"""Behavioural tests for the deterministic synthetic clinical ecosystem."""

from pathlib import Path

import pytest

from sns_patient_360.synthetic import export_journey, generate_journey, source_bundle_to_fhir


def test_journey_is_deterministic_for_fixed_seed() -> None:
    """FR-061 / NFR-070: identical seeds must reproduce identical journeys."""
    first = generate_journey(seed=360)
    second = generate_journey(seed=360)

    assert first == second
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_journey_spans_four_independent_source_systems() -> None:
    """FR-061 / FR-062: one patient journey spans four source-local identities."""
    journey = generate_journey()

    assert {bundle.source for bundle in journey.sources} == {
        "primary-care",
        "hospital",
        "laboratory",
        "pharmacy",
    }
    source_ids = {bundle.patient.source_patient_id for bundle in journey.sources}
    assert len(source_ids) == 4
    assert all(
        bundle.patient.synthetic_master_id == journey.patient.synthetic_master_id
        for bundle in journey.sources
    )


def test_each_source_contains_only_its_own_records() -> None:
    """FR-062: source exports must remain independent before Patient 360 assembly."""
    journey = generate_journey()

    for bundle in journey.sources:
        assert bundle.resources
        assert all(resource.source == bundle.source for resource in bundle.resources)
        assert all(
            resource.source_patient_id == bundle.patient.source_patient_id
            for resource in bundle.resources
        )


def test_laboratory_source_contains_longitudinal_hba1c() -> None:
    """The canonical journey includes a repeatable laboratory series for later FR-005 work."""
    journey = generate_journey()
    laboratory = next(bundle for bundle in journey.sources if bundle.source == "laboratory")

    hba1c = [
        resource
        for resource in laboratory.resources
        if resource.payload.get("code") == "HbA1c"
    ]

    assert len(hba1c) == 2
    assert [resource.payload["value"] for resource in hba1c] == [7.4, 6.8]
    assert {resource.payload["unit"] for resource in hba1c} == {"%"}


def test_source_bundle_export_is_marked_synthetic() -> None:
    """FR-060 / NFR-001: exported data is explicitly marked as synthetic."""
    bundle = generate_journey().sources[0]
    document = source_bundle_to_fhir(bundle)

    assert document["resourceType"] == "Bundle"
    assert document["type"] == "collection"
    entries = document["entry"]
    assert isinstance(entries, list)
    assert entries
    assert all(
        entry["resource"]["meta"]["tag"][0]["code"] == "synthetic" for entry in entries
    )


def test_export_writes_one_file_per_source(tmp_path: Path) -> None:
    """Independent exports are persisted separately for the future ingestion milestone."""
    created = export_journey(generate_journey(), tmp_path)

    assert {path.name for path in created} == {
        "primary-care.json",
        "hospital.json",
        "laboratory.json",
        "pharmacy.json",
    }
    assert all(path.is_file() for path in created)


def test_invalid_seed_is_rejected() -> None:
    """Generator arguments are validated rather than silently coerced."""
    with pytest.raises(TypeError):
        generate_journey(seed="360")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        generate_journey(seed=-1)
