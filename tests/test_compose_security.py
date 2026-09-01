"""Security contract tests for the local Docker Compose data services."""

from pathlib import Path


def test_database_ports_bind_to_loopback_only() -> None:
    """Development databases must not be published on all host interfaces."""
    compose = (Path(__file__).resolve().parents[1] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert '"127.0.0.1:5432:5432"' in compose
    assert '"127.0.0.1:27017:27017"' in compose
    assert '"127.0.0.1:6379:6379"' in compose
    assert '"5432:5432"' not in compose
    assert '"27017:27017"' not in compose
    assert '"6379:6379"' not in compose
