"""End-to-end test for a heterogeneous ZX artifact corpus."""

from mini_zx_library import (
    ArtifactRegistry,
    CorpusBuilder,
    DistributionMode,
    OpenQasm2Adapter,
    PyZXJsonAdapter,
    SourceDocument,
    SourceProvenance,
)


def _provenance(source_path: str) -> SourceProvenance:
    """Construct provenance for a generated test source."""
    return SourceProvenance(
        upstream_url="https://example.com/generated-corpus",
        source_path=source_path,
        license_expression="Apache-2.0",
        license_reference="https://example.com/LICENSE",
        distribution_mode=DistributionMode.BUNDLED,
    )


def test_real_adapters_compose_through_one_corpus_registry() -> None:
    qasm_source = SourceDocument(
        collection="generated-qasm",
        entry_id="bell.qasm",
        revision="1",
        content=b"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
""",
        provenance=_provenance("circuits/bell.qasm"),
    )
    graph_source = SourceDocument(
        collection="curated-graphs",
        entry_id="identity.qgraph",
        revision="1",
        content=(
            b'{"version": 2, "backend": "simple", "variable_types": {}, '
            b'"scalar": {"power2": 0, "phase": "0"}, "inputs": [0], '
            b'"outputs": [2], "edata": {}, "vertices": ['
            b'{"id": 0, "t": 0, "pos": [0, 0]}, '
            b'{"id": 1, "t": 1, "pos": [1, 0]}, '
            b'{"id": 2, "t": 0, "pos": [2, 0]}], '
            b'"edges": [[0, 1, 1], [1, 2, 1]]}'
        ),
        provenance=_provenance("graphs/identity.qgraph"),
    )

    builder = CorpusBuilder()
    qasm_artifact = builder.build(qasm_source, OpenQasm2Adapter())
    graph_artifact = builder.build(graph_source, PyZXJsonAdapter())

    repeated_qasm = builder.build(qasm_source, OpenQasm2Adapter())
    repeated_graph = builder.build(graph_source, PyZXJsonAdapter())

    assert repeated_qasm == qasm_artifact
    assert repeated_graph == graph_artifact
    assert qasm_artifact.artifact_id != graph_artifact.artifact_id

    registry = ArtifactRegistry((qasm_artifact, graph_artifact))

    assert registry.get(qasm_artifact.artifact_id) == qasm_artifact
    assert registry.get(graph_artifact.artifact_id) == graph_artifact
    assert registry.get_many(
        (graph_artifact.artifact_id, qasm_artifact.artifact_id)
    ) == (graph_artifact, qasm_artifact)

    assert registry.select(collection="generated-qasm") == (qasm_artifact,)
    assert registry.select(collection="curated-graphs") == (graph_artifact,)
    assert {artifact.artifact_id for artifact in registry.select(has_qec=False)} == {
        qasm_artifact.artifact_id,
        graph_artifact.artifact_id,
    }
