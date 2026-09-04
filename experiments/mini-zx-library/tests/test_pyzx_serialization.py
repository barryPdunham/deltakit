"""Tests documenting PyZX serialization reproducibility boundaries."""

import numpy as np
import pyzx as zx
from mini_zx_library.model import sha256_bytes
from pyzx.graph.base import BaseGraph


def _make_identity_graph(order: tuple[str, ...]) -> BaseGraph:
    """Construct the same identity diagram using a specified vertex order."""
    graph = zx.Graph()
    specifications = {
        "input": (zx.VertexType.BOUNDARY, 0, 0),
        "spider": (zx.VertexType.Z, 0, 1),
        "output": (zx.VertexType.BOUNDARY, 0, 2),
    }

    vertices = {}
    for role in order:
        vertex_type, qubit, row = specifications[role]
        vertices[role] = graph.add_vertex(
            vertex_type,
            qubit=qubit,
            row=row,
        )

    graph.add_edge((vertices["input"], vertices["spider"]))
    graph.add_edge((vertices["spider"], vertices["output"]))
    graph.set_inputs((vertices["input"],))
    graph.set_outputs((vertices["output"],))
    return graph


def _serialize(graph: BaseGraph) -> bytes:
    """Serialize a PyZX graph using its version-2 JSON representation."""
    return graph.to_json().encode()


def test_repeated_construction_has_identical_pyzx_serialization() -> None:
    order = ("input", "spider", "output")

    first = _serialize(_make_identity_graph(order))
    second = _serialize(_make_identity_graph(order))

    assert first == second
    assert sha256_bytes(first) == sha256_bytes(second)


def test_equivalent_graphs_can_have_different_pyzx_serialization() -> None:
    first_graph = _make_identity_graph(("input", "spider", "output"))
    reordered_graph = _make_identity_graph(("output", "spider", "input"))

    assert first_graph.is_well_formed()
    assert reordered_graph.is_well_formed()
    assert np.allclose(first_graph.to_matrix(), reordered_graph.to_matrix())

    first = _serialize(first_graph)
    reordered = _serialize(reordered_graph)

    assert first != reordered
    assert sha256_bytes(first) != sha256_bytes(reordered)
