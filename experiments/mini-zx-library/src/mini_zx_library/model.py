"""Immutable records for identifying raw and derived ZX-graph artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Final

_SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
_PARAMETER_PAIR_LENGTH: Final = 2


class DistributionMode(Enum):
    """How the corpus makes an upstream artifact available."""

    BUNDLED = "bundled"
    FETCHED = "fetched"
    REFERENCE_ONLY = "reference-only"


def sha256_bytes(content: bytes) -> str:
    """Return the lowercase SHA-256 digest of binary content."""
    return hashlib.sha256(content).hexdigest()


def _require_text(field_name: str, value: str) -> None:
    if not value or value.isspace():
        message = f"{field_name} must not be empty"
        raise ValueError(message)


def _require_sha256(field_name: str, value: str) -> None:
    if _SHA256_PATTERN.fullmatch(value) is None:
        message = f"{field_name} must be a lowercase 64-character SHA-256 digest"
        raise ValueError(message)


def _require_count(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"{field_name} must be a non-negative integer"
        raise ValueError(message)


def _identity_digest(kind: str, fields: dict[str, object]) -> str:
    serialized = json.dumps(
        {"kind": kind, "schema_version": 1, **fields},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"{kind}:sha256:{sha256_bytes(serialized)}"


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Documented origin, licensing, and distribution treatment."""

    upstream_url: str
    source_path: str
    license_expression: str
    license_reference: str
    distribution_mode: DistributionMode

    def __post_init__(self) -> None:
        for field_name in (
            "upstream_url",
            "source_path",
            "license_expression",
            "license_reference",
        ):
            _require_text(field_name, getattr(self, field_name))

        if not isinstance(self.distribution_mode, DistributionMode):
            message = "distribution_mode must be a DistributionMode"
            raise TypeError(message)


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    """Identity of an upstream input and the adapter used to import it."""

    collection: str
    entry_id: str
    revision: str
    source_sha256: str
    adapter_name: str
    adapter_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "collection",
            "entry_id",
            "revision",
            "adapter_name",
            "adapter_version",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_sha256("source_sha256", self.source_sha256)

    @property
    def artifact_id(self) -> str:
        """Return a deterministic identity for the imported raw artifact."""
        return _identity_digest(
            "raw",
            {
                "adapter_name": self.adapter_name,
                "adapter_version": self.adapter_version,
                "collection": self.collection,
                "entry_id": self.entry_id,
                "revision": self.revision,
                "source_sha256": self.source_sha256,
            },
        )


@dataclass(frozen=True, slots=True)
class GraphRepresentation:
    """Digest and format of a serialized ZX-graph representation."""

    format: str
    graph_sha256: str

    def __post_init__(self) -> None:
        _require_text("format", self.format)
        _require_sha256("graph_sha256", self.graph_sha256)


@dataclass(frozen=True, slots=True)
class QecSidecar:
    """QEC semantics preserved alongside, but outside, the ZX graph."""

    source_format: str
    qubit_count: int
    measurement_count: int
    detector_count: int
    observable_count: int

    def __post_init__(self) -> None:
        _require_text("source_format", self.source_format)
        for field_name in (
            "qubit_count",
            "measurement_count",
            "detector_count",
            "observable_count",
        ):
            _require_count(field_name, getattr(self, field_name))


@dataclass(frozen=True, slots=True)
class RawGraphArtifact:
    """An immutable graph imported from an upstream source."""

    source: SourceIdentity
    graph: GraphRepresentation
    provenance: SourceProvenance
    qec: QecSidecar | None = None

    @property
    def artifact_id(self) -> str:
        """Return the identity derived from the exact upstream input."""
        return self.source.artifact_id


@dataclass(frozen=True, slots=True)
class Transformation:
    """A versioned deterministic operation applied to a graph."""

    name: str
    version: str
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_text("name", self.name)
        _require_text("version", self.version)

        if not isinstance(self.parameters, tuple):
            message = "parameters must be a tuple"
            raise TypeError(message)

        for parameter in self.parameters:
            if (
                not isinstance(parameter, tuple)
                or len(parameter) != _PARAMETER_PAIR_LENGTH
            ):
                message = "each parameter must be a two-item tuple"
                raise TypeError(message)

        parameter_names = tuple(name for name, _ in self.parameters)
        if parameter_names != tuple(sorted(parameter_names)):
            message = "parameters must be sorted by name"
            raise ValueError(message)
        if len(parameter_names) != len(set(parameter_names)):
            message = "parameter names must be unique"
            raise ValueError(message)

        for name, value in self.parameters:
            _require_text("parameter name", name)
            _require_text("parameter value", value)


@dataclass(frozen=True, slots=True)
class DerivedGraphArtifact:
    """A graph produced from a parent by a recorded transformation."""

    parent_id: str
    transformation: Transformation
    graph: GraphRepresentation

    def __post_init__(self) -> None:
        _require_text("parent_id", self.parent_id)

    @property
    def artifact_id(self) -> str:
        """Return a deterministic identity including lineage and output."""
        return _identity_digest(
            "derived",
            {
                "graph_sha256": self.graph.graph_sha256,
                "parent_id": self.parent_id,
                "parameters": self.transformation.parameters,
                "transformation_name": self.transformation.name,
                "transformation_version": self.transformation.version,
            },
        )
