"""Tests for generated OpenQASM 2 ingestion."""

import pytest
from mini_zx_library import OpenQasm2Adapter
from mini_zx_library.ingestion import SourceDocument
from mini_zx_library.model import DistributionMode, SourceProvenance
from pyzx.graph.base import BaseGraph

_BELL_QUBIT_COUNT = 2


def _source(content: bytes) -> SourceDocument:
    """Construct a generated OpenQASM 2 source document."""
    return SourceDocument(
        collection="generated",
        entry_id="bell.qasm",
        revision="1",
        content=content,
        provenance=SourceProvenance(
            upstream_url="https://example.com/generated",
            source_path="circuits/bell.qasm",
            license_expression="Apache-2.0",
            license_reference="https://example.com/LICENSE",
            distribution_mode=DistributionMode.BUNDLED,
        ),
    )


def test_adapter_converts_generated_openqasm_2_to_well_formed_graph() -> None:
    content = b"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
"""

    result = OpenQasm2Adapter().convert(_source(content))
    graph = BaseGraph.from_json(result.graph_content.decode("utf-8"))

    assert result.graph_format == "pyzx-json-v2"
    assert result.qec is None
    assert graph.is_well_formed()
    assert len(graph.inputs()) == _BELL_QUBIT_COUNT
    assert len(graph.outputs()) == _BELL_QUBIT_COUNT


def test_adapter_conversion_is_deterministic() -> None:
    content = b"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];
"""

    first = OpenQasm2Adapter().convert(_source(content))
    second = OpenQasm2Adapter().convert(_source(content))

    assert first.graph_content == second.graph_content


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "valid UTF-8"),
        (
            b"""OPENQASM 3.0;
qubit[1] q;
h q[0];
""",
            "supported OpenQASM 2",
        ),
        (
            b"""qreg q[1];
h q[0];
""",
            "supported OpenQASM 2",
        ),
        (
            b"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1]
h q[0];
""",
            "supported OpenQASM 2",
        ),
    ],
)
def test_adapter_rejects_invalid_or_unsupported_qasm(
    content: bytes,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        OpenQasm2Adapter().convert(_source(content))


@pytest.mark.parametrize(
    ("statement", "operation"),
    [
        ("creg c[1];\nmeasure q[0] -> c[0];", "Measurement"),
        ("reset q[0];", "Reset"),
    ],
)
def test_adapter_rejects_non_unitary_operations(
    statement: str,
    operation: str,
) -> None:
    content = f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
{statement}
""".encode()

    with pytest.raises(ValueError, match=operation):
        OpenQasm2Adapter().convert(_source(content))
