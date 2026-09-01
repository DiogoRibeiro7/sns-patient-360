"""Security contract tests for the local Docker Compose services."""

from pathlib import Path


def _compose_text() -> str:
    """Return the local Docker Compose definition as text."""
    return (Path(__file__).resolve().parents[1] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )


def test_published_ports_bind_to_loopback_only() -> None:
    """Development data/imaging services must not publish ports on all interfaces."""
    compose = _compose_text()

    loopback_ports = (
        "5432:5432",
        "27017:27017",
        "6379:6379",
        "9000:9000",
        "9001:9001",
        "4242:4242",
        "8042:8042",
    )
    for port_mapping in loopback_ports:
        assert f'"127.0.0.1:{port_mapping}"' in compose
        assert f'"{port_mapping}"' not in compose


def test_imaging_stack_has_explicit_local_credentials_and_dicomweb() -> None:
    """The reference PACS/object-store stack must not be anonymous by default."""
    compose = _compose_text()

    assert "DICOM_WEB_PLUGIN_ENABLED" in compose
    assert "AWS_S3_STORAGE_PLUGIN_ENABLED" in compose
    assert "ORTHANC__REGISTERED_USERS" in compose
    assert "MINIO_ROOT_USER" in compose
    assert "MINIO_ROOT_PASSWORD" in compose
    assert "orthanc-dicom" in compose
