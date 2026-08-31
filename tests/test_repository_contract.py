from pathlib import Path


REQUIRED_DOCS: tuple[str, ...] = (
    "docs/architecture/product-scope.md",
    "docs/data-model/fhir-scope.md",
    "docs/security/threat-model.md",
    "docs/adr/0001-use-fhir-as-interoperability-contract.md",
    "docs/adr/0002-separate-fhir-store-from-patient-360-read-model.md",
    "docs/adr/0003-synthetic-data-only.md",
)


def test_required_architecture_documents_exist() -> None:
    """Ensure the architecture contract remains part of the repository baseline."""
    repository_root = Path(__file__).resolve().parents[1]

    missing_documents = [
        relative_path
        for relative_path in REQUIRED_DOCS
        if not (repository_root / relative_path).is_file()
    ]

    assert not missing_documents, f"Missing architecture documents: {missing_documents}"
