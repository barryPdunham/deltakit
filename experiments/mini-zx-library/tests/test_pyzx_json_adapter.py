"""Tests for graph-native PyZX JSON ingestion."""

import pytest
from mini_zx_library import PyZXJsonAdapter
from mini_zx_library.ingestion import SourceDocument
from mini_zx_library.model import DistributionMode, SourceProvenance


def _source(content: bytes) -> SourceDocument:
    """Construct a graph-native source document."""
    return SourceDocument(
        collection="curated",
        entry_id="example.qgraph",
        revision="1",
        content=content,
        provenance=SourceProvenance(
            upstream_url="https://example.com/graphs",
            source_path="graphs/example.qgraph",
            license_expression="Apache-2.0",
            license_reference="https://example.com/graphs/LICENSE",
            distribution_mode=DistributionMode.REFERENCE_ONLY,
        ),
    )


def test_adapter_preserves_valid_version_2_source_bytes() -> None:
    content = (
        b'{"version": 2, "backend": "simple", "variable_types": {}, '
        b'"scalar": {"power2": 0, "phase": "0"}, "inputs": [0], '
        b'"outputs": [2], "edata": {}, "vertices": ['
        b'{"id": 0, "t": 0, "pos": [0, 0]}, '
        b'{"id": 1, "t": 1, "pos": [1, 0]}, '
        b'{"id": 2, "t": 0, "pos": [2, 0]}], '
        b'"edges": [[0, 1, 1], [1, 2, 1]]}\n'
    )

    result = PyZXJsonAdapter().convert(_source(content))

    assert result.graph_format == "pyzx-json-v2"
    assert result.graph_content is content
    assert result.qec is None


def test_adapter_accepts_well_formed_graph_without_boundaries() -> None:
    content = (
        b'{"version": 2, "backend": "simple", "variable_types": {}, '
        b'"scalar": {"power2": 0, "phase": "0"}, "inputs": [], '
        b'"outputs": [], "edata": {}, "vertices": [], "edges": []}'
    )

    result = PyZXJsonAdapter().convert(_source(content))

    assert result.graph_content is content


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "valid UTF-8"),
        (b"{", "valid JSON"),
        (b"[]", "JSON object"),
        (b"{}", "version 2"),
        (b'{"version": 3}', "version 2"),
        (
            b'{"version": 2, "backend": "simple", "vertices": [], '
            b'"edges": [[0, 1, 1]]}',
            "could not be parsed",
        ),
    ],
)
def test_adapter_rejects_invalid_serialization(
    content: bytes,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        PyZXJsonAdapter().convert(_source(content))


def test_adapter_rejects_parseable_but_ill_formed_graph() -> None:
    content = (
        b'{"version": 2, "backend": "simple", "variable_types": {}, '
        b'"scalar": {"power2": 0, "phase": "0"}, "inputs": [0], '
        b'"outputs": [], "edata": {}, "vertices": ['
        b'{"id": 0, "t": 0, "pos": [0, 0]}], "edges": []}'
    )

    with pytest.raises(ValueError, match="well-formed"):
        PyZXJsonAdapter().convert(_source(content))
