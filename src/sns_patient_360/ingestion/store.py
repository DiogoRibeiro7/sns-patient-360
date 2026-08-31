"""Transactional canonical clinical store backed by SQLAlchemy."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, MetaData, String, Table, Column, Engine, create_engine, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from sns_patient_360.ingestion.models import (
    CanonicalClinicalResource,
    CanonicalPatient,
    ProvenanceRecord,
)

_METADATA = MetaData()

_PATIENTS = Table(
    "canonical_patients",
    _METADATA,
    Column("canonical_patient_id", String, primary_key=True),
    Column("synthetic_national_health_id", String, unique=True, nullable=False),
)

_ALIASES = Table(
    "patient_source_aliases",
    _METADATA,
    Column("source_system", String, primary_key=True),
    Column("source_patient_id", String, primary_key=True),
    Column("canonical_patient_id", String, nullable=False),
)

_RESOURCES = Table(
    "clinical_resources",
    _METADATA,
    Column("source_system", String, primary_key=True),
    Column("resource_type", String, primary_key=True),
    Column("resource_id", String, primary_key=True),
    Column("version_id", String, primary_key=True),
    Column("canonical_patient_id", String, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
)


class CanonicalClinicalStore:
    """Persist canonical identities and versioned clinical resources transactionally."""

    def __init__(self, database_url: str = "sqlite+pysqlite:///:memory:") -> None:
        if not isinstance(database_url, str):
            raise TypeError("database_url must be a string")
        self._engine: Engine = create_engine(database_url, future=True)
        _METADATA.create_all(self._engine)

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """Open a transaction that commits atomically or rolls back on error."""
        with self._engine.begin() as connection:
            yield connection

    def resolve_patient_by_identifier(
        self,
        connection: Connection,
        synthetic_national_health_id: str,
    ) -> CanonicalPatient | None:
        """Resolve an existing canonical patient by the shared synthetic identifier."""
        row = connection.execute(
            select(_PATIENTS).where(
                _PATIENTS.c.synthetic_national_health_id == synthetic_national_health_id
            )
        ).mappings().one_or_none()
        if row is None:
            return None
        return self.get_patient(connection, str(row["canonical_patient_id"]))

    def get_patient(self, connection: Connection, canonical_patient_id: str) -> CanonicalPatient:
        """Return one canonical patient and all known source-local aliases."""
        patient = connection.execute(
            select(_PATIENTS).where(
                _PATIENTS.c.canonical_patient_id == canonical_patient_id
            )
        ).mappings().one()
        aliases = connection.execute(
            select(_ALIASES).where(_ALIASES.c.canonical_patient_id == canonical_patient_id)
        ).mappings().all()
        return CanonicalPatient(
            canonical_patient_id=canonical_patient_id,
            synthetic_national_health_id=str(patient["synthetic_national_health_id"]),
            source_patient_ids={
                str(alias["source_system"]): str(alias["source_patient_id"])
                for alias in aliases
            },
        )

    def create_patient(
        self,
        connection: Connection,
        canonical_patient_id: str,
        synthetic_national_health_id: str,
    ) -> CanonicalPatient:
        """Create a canonical patient identity."""
        connection.execute(
            _PATIENTS.insert().values(
                canonical_patient_id=canonical_patient_id,
                synthetic_national_health_id=synthetic_national_health_id,
            )
        )
        return CanonicalPatient(
            canonical_patient_id=canonical_patient_id,
            synthetic_national_health_id=synthetic_national_health_id,
            source_patient_ids={},
        )

    def attach_alias(
        self,
        connection: Connection,
        source_system: str,
        source_patient_id: str,
        canonical_patient_id: str,
    ) -> None:
        """Attach a source-local patient identifier to a canonical patient idempotently."""
        existing = connection.execute(
            select(_ALIASES).where(
                (_ALIASES.c.source_system == source_system)
                & (_ALIASES.c.source_patient_id == source_patient_id)
            )
        ).mappings().one_or_none()
        if existing is None:
            connection.execute(
                _ALIASES.insert().values(
                    source_system=source_system,
                    source_patient_id=source_patient_id,
                    canonical_patient_id=canonical_patient_id,
                )
            )
            return
        if str(existing["canonical_patient_id"]) != canonical_patient_id:
            raise ValueError("source patient alias is already attached to another canonical patient")

    def resource_exists(
        self,
        connection: Connection,
        resource: CanonicalClinicalResource,
    ) -> bool:
        """Return whether the exact source resource version already exists."""
        row = connection.execute(
            select(_RESOURCES.c.payload).where(
                (_RESOURCES.c.source_system == resource.source_system)
                & (_RESOURCES.c.resource_type == resource.resource_type)
                & (_RESOURCES.c.resource_id == resource.resource_id)
                & (_RESOURCES.c.version_id == resource.version_id)
            )
        ).one_or_none()
        if row is None:
            return False
        existing_payload = row[0]
        if existing_payload != resource.payload:
            raise ValueError(
                "conflicting payload for an existing source resource version; refusing overwrite"
            )
        return True

    def insert_resource(
        self,
        connection: Connection,
        resource: CanonicalClinicalResource,
    ) -> None:
        """Insert one validated source resource version without overwriting existing facts."""
        try:
            connection.execute(
                _RESOURCES.insert().values(
                    source_system=resource.source_system,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    version_id=resource.version_id,
                    canonical_patient_id=resource.canonical_patient_id,
                    payload=json.loads(json.dumps(resource.payload, sort_keys=True)),
                    ingested_at=resource.provenance.ingested_at,
                )
            )
        except IntegrityError as exc:
            raise ValueError("resource version already exists") from exc

    def list_resources(self, canonical_patient_id: str) -> tuple[CanonicalClinicalResource, ...]:
        """List all preserved resource versions for one canonical patient."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_RESOURCES).where(
                    _RESOURCES.c.canonical_patient_id == canonical_patient_id
                )
            ).mappings().all()

        return tuple(
            CanonicalClinicalResource(
                canonical_patient_id=str(row["canonical_patient_id"]),
                resource_type=str(row["resource_type"]),
                resource_id=str(row["resource_id"]),
                version_id=str(row["version_id"]),
                source_system=str(row["source_system"]),
                payload=dict(row["payload"]),
                provenance=ProvenanceRecord(
                    source_system=str(row["source_system"]),
                    source_patient_id=self.source_patient_id_for(
                        str(row["source_system"]), str(row["canonical_patient_id"])
                    ),
                    resource_type=str(row["resource_type"]),
                    resource_id=str(row["resource_id"]),
                    version_id=str(row["version_id"]),
                    ingested_at=row["ingested_at"],
                ),
            )
            for row in rows
        )

    def source_patient_id_for(self, source_system: str, canonical_patient_id: str) -> str:
        """Return the source-local patient identifier for provenance reconstruction."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(_ALIASES.c.source_patient_id).where(
                    (_ALIASES.c.source_system == source_system)
                    & (_ALIASES.c.canonical_patient_id == canonical_patient_id)
                )
            ).one()
        return str(row[0])

    def patient_count(self) -> int:
        """Return the number of canonical patients."""
        with self._engine.connect() as connection:
            return len(connection.execute(select(_PATIENTS.c.canonical_patient_id)).all())

    def resource_count(self) -> int:
        """Return the number of preserved source resource versions."""
        with self._engine.connect() as connection:
            return len(connection.execute(select(_RESOURCES.c.resource_id)).all())
