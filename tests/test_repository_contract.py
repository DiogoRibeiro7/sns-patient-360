"""Repository-level architecture and requirements contract tests."""

from pathlib import Path


REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/product-scope.md",
    "docs/architecture/system-architecture.md",
    "docs/architecture/requirements.md",
    "docs/architecture/imaging-requirements.md",
    "docs/architecture/ingestion-persistence.md",
    "docs/architecture/imaging.md",
    "docs/data-model/fhir-scope.md",
    "docs/security/threat-model.md",
    "docs/adr/0001-use-fhir-as-interoperability-contract.md",
    "docs/adr/0002-separate-fhir-store-from-patient-360-read-model.md",
    "docs/adr/0003-synthetic-data-only.md",
    "docs/adr/0004-use-polyglot-persistence.md",
    "docs/adr/0005-use-dicom-for-diagnostic-imaging.md",
)

MERMAID_DOCS: tuple[str, ...] = (
    "README.md",
    "docs/architecture/system-architecture.md",
    "docs/architecture/ingestion-persistence.md",
    "docs/architecture/imaging.md",
    "docs/data-model/fhir-scope.md",
)

REQUIRED_REQUIREMENT_IDS: tuple[str, ...] = (
    "FR-001",
    "FR-010",
    "FR-020",
    "FR-060",
    "NFR-001",
    "NFR-010",
    "NFR-020",
    "NFR-060",
    "NFR-063",
    "NFR-070",
)

REQUIRED_IMAGING_REQUIREMENT_IDS: tuple[str, ...] = (
    "FR-070",
    "FR-073",
    "FR-074",
    "FR-079",
    "NFR-100",
    "NFR-102",
    "NFR-110",
    "NFR-120",
    "NFR-140",
)


def _repository_root() -> Path:
    """Return the repository root used by contract tests."""
    return Path(__file__).resolve().parents[1]


def test_required_architecture_documents_exist() -> None:
    """Ensure the architecture contract remains part of the repository baseline."""
    repository_root = _repository_root()
    missing_documents = [
        relative_path
        for relative_path in REQUIRED_DOCS
        if not (repository_root / relative_path).is_file()
    ]
    assert not missing_documents, f"Missing architecture documents: {missing_documents}"


def test_architecture_documents_use_mermaid() -> None:
    """Require Mermaid diagrams in versioned architecture documentation."""
    repository_root = _repository_root()
    missing_mermaid = [
        relative_path
        for relative_path in MERMAID_DOCS
        if "```mermaid" not in (repository_root / relative_path).read_text(encoding="utf-8")
    ]
    assert not missing_mermaid, f"Architecture documents without Mermaid: {missing_mermaid}"


def test_requirements_have_stable_contract_identifiers() -> None:
    """Ensure the baseline and imaging requirements retain representative stable IDs."""
    repository_root = _repository_root()
    requirements = (repository_root / "docs/architecture/requirements.md").read_text(
        encoding="utf-8"
    )
    imaging_requirements = (
        repository_root / "docs/architecture/imaging-requirements.md"
    ).read_text(encoding="utf-8")

    missing_ids = [
        requirement_id
        for requirement_id in REQUIRED_REQUIREMENT_IDS
        if requirement_id not in requirements
    ]
    missing_imaging_ids = [
        requirement_id
        for requirement_id in REQUIRED_IMAGING_REQUIREMENT_IDS
        if requirement_id not in imaging_requirements
    ]

    assert not missing_ids, f"Missing requirement identifiers: {missing_ids}"
    assert not missing_imaging_ids, (
        f"Missing imaging requirement identifiers: {missing_imaging_ids}"
    )
