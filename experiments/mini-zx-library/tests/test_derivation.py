"""Tests for deterministic graph transformation and lineage."""

import numpy as np
import pytest
import pyzx as zx
from mini_zx_library import (
    DerivationBuilder,
    DerivedGraphResult,
    DistributionMode,
    GraphDigestMismatchError,
    GraphRepresentation,
    PyZXSpiderSimplifier,
    RawGraphArtifact,
    SourceIdentity,
    SourceProvenance,
    Transformation,
    sha256_bytes,
)
from mini_zx_library.derivation import _TransformationResult
from pyzx.graph.base import BaseGraph


def _reducible_graph_content() -> bytes:
    """Serialize a well-formed graph containing adjacent Z spiders."""
    graph = zx.Graph()

    input_vertex = graph.add_vertex(zx.VertexType.BOUNDARY, qubit=0, row=0)
    first_spider = graph.add_vertex(zx.VertexType.Z, qubit=0, row=1)
    second_spider = graph.add_vertex(zx.VertexType.Z, qubit=0, row=2)
    output_vertex = graph.add_vertex(zx.VertexType.BOUNDARY, qubit=0, row=3)

    graph.add_edge((input_vertex, first_spider))
    graph.add_edge((first_spider, second_spider))
    graph.add_edge((second_spider, output_vertex))
    graph.set_inputs((input_vertex,))
    graph.set_outputs((output_vertex,))

    return graph.to_json().encode("utf-8")


def _parent(graph_content: bytes) -> RawGraphArtifact:
    """Construct a raw parent artifact matching serialized graph content."""
    return RawGraphArtifact(
        source=SourceIdentity(
            collection="generated",
            entry_id="reducible.qgraph",
            revision="1",
            source_sha256=sha256_bytes(graph_content),
            adapter_name="fixture",
            adapter_version="1",
        ),
        graph=GraphRepresentation(
            format="pyzx-json-v2",
            graph_sha256=sha256_bytes(graph_content),
        ),
        provenance=SourceProvenance(
            upstream_url="https://example.com/generated",
            source_path="graphs/reducible.qgraph",
            license_expression="Apache-2.0",
            license_reference="https://example.com/LICENSE",
            distribution_mode=DistributionMode.BUNDLED,
        ),
    )


def test_spider_simplification_builds_semantically_equivalent_derivation() -> None:
    parent_content = _reducible_graph_content()
    parent = _parent(parent_content)

    result = DerivationBuilder().build(
        parent,
        parent_content,
        PyZXSpiderSimplifier(),
    )

    original_graph = BaseGraph.from_json(parent_content.decode("utf-8"))
    derived_graph = BaseGraph.from_json(result.graph_content.decode("utf-8"))

    assert isinstance(result, DerivedGraphResult)
    assert result.artifact.parent_id == parent.artifact_id
    assert result.artifact.transformation == Transformation(
        name="pyzx-spider-simp",
        version="1",
    )
    assert result.artifact.graph.format == "pyzx-json-v2"
    assert result.artifact.graph.graph_sha256 == sha256_bytes(result.graph_content)
    assert derived_graph.is_well_formed()
    assert derived_graph.num_vertices() < original_graph.num_vertices()
    assert np.allclose(original_graph.to_matrix(), derived_graph.to_matrix())
    assert parent_content == _reducible_graph_content()


def test_spider_simplification_is_deterministic() -> None:
    parent_content = _reducible_graph_content()
    parent = _parent(parent_content)
    builder = DerivationBuilder()
    transformer = PyZXSpiderSimplifier()

    first = builder.build(parent, parent_content, transformer)
    second = builder.build(parent, parent_content, transformer)

    assert first == second
    assert first.graph_content == second.graph_content
    assert first.artifact.artifact_id == second.artifact.artifact_id


def test_spider_simplification_requires_explicit_version_2_json() -> None:
    parent_content = b"{}"
    parent = _parent(parent_content)

    with pytest.raises(ValueError, match="version 2"):
        DerivationBuilder().build(
            parent,
            parent_content,
            PyZXSpiderSimplifier(),
        )


class _TransformerThatMustNotRun:
    """Fail if derivation begins before parent-content verification."""

    name = "must-not-run"
    version = "1"
    parameters: tuple[tuple[str, str], ...] = ()

    def transform(self, graph_content: bytes) -> _TransformationResult:
        del graph_content
        message = "transformer ran before parent-content verification"
        raise AssertionError(message)


def test_builder_rejects_content_that_does_not_match_parent() -> None:
    parent_content = _reducible_graph_content()
    parent = _parent(parent_content)

    with pytest.raises(GraphDigestMismatchError, match="does not match"):
        DerivationBuilder().build(
            parent,
            b"different graph content",
            _TransformerThatMustNotRun(),
        )
