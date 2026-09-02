"""Tests for immutable artifact identity records."""

from dataclasses import FrozenInstanceError

import pytest
from mini_zx_library.model import (
    DerivedGraphArtifact,
    GraphRepresentation,
    QecSidecar,
    RawGraphArtifact,
    SourceIdentity,
    Transformation,
    sha256_bytes,
)

_EXPECTED_DETECTOR_COUNT = 12


def make_source(adapter_version: str = "1") -> SourceIdentity:
    """Return a representative deterministic source identity."""
    return SourceIdentity(
        collection="benchpress",
        entry_id="example.qasm",
        revision="abc123",
        source_sha256=sha256_bytes(b"OPENQASM example"),
        adapter_name="qasm",
        adapter_version=adapter_version,
    )


def make_graph(content: bytes = b"serialized graph") -> GraphRepresentation:
    """Return a representative serialized graph record."""
    return GraphRepresentation(
        format="pyzx-json",
        graph_sha256=sha256_bytes(content),
    )


def test_source_identity_is_deterministic() -> None:
    first = make_source()
    second = make_source()

    assert first.artifact_id == second.artifact_id
    assert first.artifact_id.startswith("raw:sha256:")


def test_adapter_version_changes_raw_identity() -> None:
    assert make_source("1").artifact_id != make_source("2").artifact_id


def test_graph_digest_is_evidence_not_raw_identity() -> None:
    source = make_source()
    first = RawGraphArtifact(source=source, graph=make_graph(b"first"))
    second = RawGraphArtifact(source=source, graph=make_graph(b"second"))

    assert first.artifact_id == second.artifact_id
    assert first.graph.graph_sha256 != second.graph.graph_sha256


def test_qec_sidecar_preserves_counts() -> None:
    sidecar = QecSidecar(
        source_format="stim",
        qubit_count=17,
        measurement_count=24,
        detector_count=_EXPECTED_DETECTOR_COUNT,
        observable_count=1,
    )
    artifact = RawGraphArtifact(
        source=make_source(),
        graph=make_graph(),
        qec=sidecar,
    )

    assert artifact.qec is not None
    assert artifact.qec == sidecar
    assert artifact.qec.detector_count == _EXPECTED_DETECTOR_COUNT


@pytest.mark.parametrize("invalid_count", [-1, True, 1.5])
def test_qec_sidecar_rejects_invalid_counts(
    invalid_count: object,
) -> None:
    with pytest.raises(ValueError, match="non-negative integer"):
        QecSidecar(
            source_format="stim",
            qubit_count=invalid_count,  # type: ignore[arg-type]
            measurement_count=0,
            detector_count=0,
            observable_count=0,
        )


def test_source_records_are_immutable() -> None:
    source = make_source()

    with pytest.raises(FrozenInstanceError):
        source.collection = "qecirc"  # type: ignore[misc]


def test_transformation_requires_canonical_parameter_order() -> None:
    with pytest.raises(ValueError, match="sorted by name"):
        Transformation(
            name="simplify",
            version="1",
            parameters=(("z", "last"), ("a", "first")),
        )


def test_transformation_rejects_mutable_parameters() -> None:
    with pytest.raises(TypeError, match="must be a tuple"):
        Transformation(
            name="simplify",
            version="1",
            parameters=[("rule", "spider")],  # type: ignore[arg-type]
        )


def test_derived_identity_includes_lineage_and_output() -> None:
    parent = RawGraphArtifact(
        source=make_source(),
        graph=make_graph(),
    )
    transformation = Transformation(
        name="simplify",
        version="1",
        parameters=(("rule", "spider"),),
    )

    first = DerivedGraphArtifact(
        parent_id=parent.artifact_id,
        transformation=transformation,
        graph=make_graph(b"derived output"),
    )
    repeated = DerivedGraphArtifact(
        parent_id=parent.artifact_id,
        transformation=transformation,
        graph=make_graph(b"derived output"),
    )
    different_output = DerivedGraphArtifact(
        parent_id=parent.artifact_id,
        transformation=transformation,
        graph=make_graph(b"different output"),
    )

    assert first.artifact_id == repeated.artifact_id
    assert first.artifact_id.startswith("derived:sha256:")
    assert first.artifact_id != different_output.artifact_id
