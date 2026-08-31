"""Integration tests for canonical FHIR ingestion and longitudinal persistence."""

from copy import deepcopy

from sns_patient_360.ingestion import CanonicalClinicalStore, IngestionService
from sns_patient_360.synthetic import generate_journey, source_bundle_to_fhir


def _documents() -> list[dict[str, object]]:
    journey = generate_journey(seed=360)
    return [source_bundle_to_fhir(bundle) for bundle in journey.sources]


def test_four_sources_resolve_to_one_canonical_patient() -> None:
    """FR-001 / FR-010 / FR-020: four local identities resolve to one patient."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)

    results = [service.ingest_bundle(document) for document in _documents()]

    assert all(result.rejected == 0 for result in results)
    assert len({result.canonical_patient_id for result in results}) == 1
    assert store.patient_count() == 1
    assert store.resource_count() == 17

    canonical_id = results[0].canonical_patient_id
    assert canonical_id is not None
    resources = store.list_resources(canonical_id)
    assert {resource.provenance.source_system for resource in resources} == {
        "primary-care",
        "hospital",
        "laboratory",
        "pharmacy",
    }
    assert len({resource.provenance.source_patient_id for resource in resources}) == 4


def test_reingestion_is_idempotent() -> None:
    """FR-012 / NFR-042: replaying source bundles must not duplicate clinical facts."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)
    documents = _documents()

    first = [service.ingest_bundle(document) for document in documents]
    initial_count = store.resource_count()
    second = [service.ingest_bundle(document) for document in documents]

    assert sum(result.accepted for result in first) == 17
    assert sum(result.accepted for result in second) == 0
    assert sum(result.duplicates for result in second) == 17
    assert store.resource_count() == initial_count == 17


def test_cross_source_assertions_are_preserved_independently() -> None:
    """FR-014: similar medication assertions from different sources are not overwritten."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)
    results = [service.ingest_bundle(document) for document in _documents()]
    canonical_id = results[0].canonical_patient_id

    assert canonical_id is not None
    ramipril = [
        resource
        for resource in store.list_resources(canonical_id)
        if resource.resource_type == "MedicationRequest"
        and resource.payload.get("medication") == "ramipril"
    ]
    assert len(ramipril) == 2
    assert {resource.source_system for resource in ramipril} == {"primary-care", "pharmacy"}


def test_new_source_version_is_preserved() -> None:
    """FR-013: a new source version is appended instead of replacing the old version."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)
    documents = _documents()
    for document in documents:
        service.ingest_bundle(document)

    hospital = deepcopy(documents[1])
    entries = hospital["entry"]
    assert isinstance(entries, list)
    observation = next(
        entry["resource"]
        for entry in entries
        if entry["resource"]["resourceType"] == "Observation"
    )
    observation["meta"]["versionId"] = "2"
    observation["value"] = 8.0

    result = service.ingest_bundle(hospital)

    assert result.rejected == 0
    assert result.accepted == 1
    assert store.resource_count() == 18


def test_same_version_mutation_is_rejected_without_overwrite() -> None:
    """FR-014 / NFR-021: conflicting same-version payloads fail closed."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)
    documents = _documents()
    for document in documents:
        service.ingest_bundle(document)

    hospital = deepcopy(documents[1])
    entries = hospital["entry"]
    assert isinstance(entries, list)
    observation = next(
        entry["resource"]
        for entry in entries
        if entry["resource"]["resourceType"] == "Observation"
    )
    observation["value"] = 99.0

    result = service.ingest_bundle(hospital)

    assert result.rejected == 1
    assert result.accepted == 0
    assert store.resource_count() == 17
    assert store.ingestion_event_count("rejected") == 1


def test_invalid_bundle_is_rejected_and_audited() -> None:
    """FR-011: invalid resources do not mutate clinical state and are auditable."""
    store = CanonicalClinicalStore()
    service = IngestionService(store)
    document = deepcopy(_documents()[0])
    entries = document["entry"]
    assert isinstance(entries, list)
    entries[0]["resource"]["meta"]["tag"] = []

    result = service.ingest_bundle(document)

    assert result.rejected == 1
    assert store.patient_count() == 0
    assert store.resource_count() == 0
    assert store.ingestion_event_count("rejected") == 1
