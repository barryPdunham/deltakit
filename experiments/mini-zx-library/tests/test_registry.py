"""Tests for bulk artifact registration and retrieval."""

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
from mini_zx_library.registry import (
    ArtifactConflictError,
    ArtifactKind,
    ArtifactNotFoundError,
    ArtifactRegistry,
)


def make_source(
    *,
    collection: str = "benchpress",
    entry_id: str = "example.qasm",
) -> SourceIdentity:
    """Return a representative source identity."""
    return SourceIdentity(
        collection=collection,
        entry_id=entry_id,
        revision="abc123",
        source_sha256=sha256_bytes(entry_id.encode()),
        adapter_name="fixture",
        adapter_version="1",
    )


def make_graph(content: bytes) -> GraphRepresentation:
    """Return a representative graph representation."""
    return GraphRepresentation(
        format="pyzx-json",
        graph_sha256=sha256_bytes(content),
    )


def make_raw(
    *,
    collection: str = "benchpress",
    entry_id: str = "example.qasm",
    graph_content: bytes = b"raw graph",
    has_qec: bool = False,
) -> RawGraphArtifact:
    """Return a representative raw artifact."""
    sidecar = None
    if has_qec:
        sidecar = QecSidecar(
            source_format="stim",
            qubit_count=17,
            measurement_count=24,
            detector_count=12,
            observable_count=1,
        )

    return RawGraphArtifact(
        source=make_source(
            collection=collection,
            entry_id=entry_id,
        ),
        graph=make_graph(graph_content),
        qec=sidecar,
    )


def make_derived(
    parent: RawGraphArtifact,
    graph_content: bytes = b"derived graph",
) -> DerivedGraphArtifact:
    """Return a representative derived artifact."""
    return DerivedGraphArtifact(
        parent_id=parent.artifact_id,
        transformation=Transformation(
            name="simplify",
            version="1",
            parameters=(("rule", "spider"),),
        ),
        graph=make_graph(graph_content),
    )


def test_register_and_repeat_identical_artifact() -> None:
    artifact = make_raw()
    registry = ArtifactRegistry()

    registry.register(artifact)
    registry.register(artifact)

    assert registry.all() == (artifact,)
    assert registry.get(artifact.artifact_id) is artifact


def test_register_rejects_identity_conflict() -> None:
    first = make_raw(graph_content=b"first graph")
    conflicting = make_raw(graph_content=b"different graph")
    registry = ArtifactRegistry((first,))

    assert first.artifact_id == conflicting.artifact_id
    assert first.graph != conflicting.graph

    with pytest.raises(ArtifactConflictError, match="identity conflict"):
        registry.register(conflicting)


def test_get_reports_missing_artifact() -> None:
    registry = ArtifactRegistry()

    with pytest.raises(ArtifactNotFoundError, match="artifact not found"):
        registry.get("raw:sha256:missing")


def test_get_many_preserves_requested_order() -> None:
    first = make_raw(entry_id="first.qasm")
    second = make_raw(entry_id="second.qasm")
    registry = ArtifactRegistry((first, second))

    result = registry.get_many(
        (second.artifact_id, first.artifact_id),
    )

    assert result == (second, first)


def test_all_uses_deterministic_identity_order() -> None:
    first = make_raw(entry_id="first.qasm")
    second = make_raw(entry_id="second.qasm")
    registry = ArtifactRegistry((second, first))

    expected = tuple(sorted((first, second), key=lambda artifact: artifact.artifact_id))

    assert registry.all() == expected


def test_select_filters_artifact_kind() -> None:
    raw = make_raw()
    derived = make_derived(raw)
    registry = ArtifactRegistry((raw, derived))

    assert registry.select(kind=ArtifactKind.RAW) == (raw,)
    assert registry.select(kind=ArtifactKind.DERIVED) == (derived,)


def test_select_collection_returns_only_raw_source_artifacts() -> None:
    benchpress = make_raw(
        collection="benchpress",
        entry_id="benchpress.qasm",
    )
    qecirc = make_raw(
        collection="qecirc",
        entry_id="qecirc.stim",
    )
    derived = make_derived(benchpress)
    registry = ArtifactRegistry((benchpress, qecirc, derived))

    assert registry.select(collection="benchpress") == (benchpress,)
    assert registry.select(collection="qecirc") == (qecirc,)


def test_select_filters_qec_sidecars() -> None:
    qec = make_raw(
        collection="qecirc",
        entry_id="qec.stim",
        has_qec=True,
    )
    plain = make_raw(entry_id="plain.qasm")
    derived = make_derived(plain)
    registry = ArtifactRegistry((qec, plain, derived))

    with_qec = registry.select(has_qec=True)
    without_qec = registry.select(has_qec=False)

    assert with_qec == (qec,)
    assert set(without_qec) == {plain, derived}
