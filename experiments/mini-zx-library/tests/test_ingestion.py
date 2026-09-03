"""Tests for centralized artifact construction."""

import mini_zx_library
import pytest
from mini_zx_library.ingestion import (
    CorpusBuilder,
    SourceDocument,
    _ImportResult,
)
from mini_zx_library.model import QecSidecar, sha256_bytes
from mini_zx_library.registry import ArtifactConflictError, ArtifactRegistry


class _QasmFixtureAdapter:
    """Represent an independently implemented QASM adapter."""

    name = "qasm-fixture"
    version = "1"

    def convert(self, source: SourceDocument) -> _ImportResult:
        return _ImportResult(
            graph_format="pyzx-json",
            graph_content=b"qasm-graph:" + source.content,
        )


class _StimFixtureAdapter:
    """Represent an independently implemented Stim adapter."""

    name = "stim-fixture"
    version = "1"

    def convert(self, source: SourceDocument) -> _ImportResult:
        return _ImportResult(
            graph_format="pyzx-json",
            graph_content=b"stim-graph:" + source.content,
            qec=QecSidecar(
                source_format="stim",
                qubit_count=17,
                measurement_count=24,
                detector_count=12,
                observable_count=1,
            ),
        )


class _VersionedFixtureAdapter:
    """Represent an adapter whose version can change."""

    name = "versioned-fixture"

    def __init__(
        self,
        *,
        version: str,
        graph_content: bytes = b"graph",
    ) -> None:
        self.version = version
        self.graph_content = graph_content

    def convert(self, source: SourceDocument) -> _ImportResult:
        del source
        return _ImportResult(
            graph_format="pyzx-json",
            graph_content=self.graph_content,
        )


def test_builder_applies_shared_hashing_to_qasm_adapter() -> None:
    source = SourceDocument(
        collection="benchpress",
        entry_id="example.qasm",
        revision="abc123",
        content=b"OPENQASM example",
    )

    artifact = CorpusBuilder().build(source, _QasmFixtureAdapter())

    assert artifact.source.source_sha256 == sha256_bytes(source.content)
    assert artifact.graph.graph_sha256 == sha256_bytes(b"qasm-graph:" + source.content)
    assert artifact.source.adapter_name == _QasmFixtureAdapter.name
    assert artifact.qec is None


def test_builder_preserves_stim_qec_sidecar() -> None:
    source = SourceDocument(
        collection="qecirc",
        entry_id="example.stim",
        revision="def456",
        content=b"H 0\nM 0\nDETECTOR rec[-1]",
    )

    artifact = CorpusBuilder().build(source, _StimFixtureAdapter())

    assert artifact.source.source_sha256 == sha256_bytes(source.content)
    assert artifact.graph.graph_sha256 == sha256_bytes(b"stim-graph:" + source.content)
    assert artifact.qec is not None
    assert artifact.qec.source_format == "stim"


def test_adapter_version_changes_artifact_identity() -> None:
    source = SourceDocument(
        collection="fixtures",
        entry_id="versioned.source",
        revision="revision",
        content=b"source",
    )
    builder = CorpusBuilder()

    first = builder.build(
        source,
        _VersionedFixtureAdapter(version="1"),
    )
    second = builder.build(
        source,
        _VersionedFixtureAdapter(version="2"),
    )

    assert first.artifact_id != second.artifact_id


def test_registry_detects_conversion_drift() -> None:
    source = SourceDocument(
        collection="fixtures",
        entry_id="drift.source",
        revision="revision",
        content=b"unchanged source",
    )
    builder = CorpusBuilder()

    first = builder.build(
        source,
        _VersionedFixtureAdapter(
            version="1",
            graph_content=b"first graph",
        ),
    )
    drifted = builder.build(
        source,
        _VersionedFixtureAdapter(
            version="1",
            graph_content=b"different graph",
        ),
    )

    assert first.artifact_id == drifted.artifact_id
    assert first.graph != drifted.graph

    registry = ArtifactRegistry((first,))
    with pytest.raises(ArtifactConflictError, match="identity conflict"):
        registry.register(drifted)


def test_internal_import_result_is_not_exported() -> None:
    assert not hasattr(mini_zx_library, "_ImportResult")
