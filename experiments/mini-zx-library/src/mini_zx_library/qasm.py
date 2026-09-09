"""Unitary OpenQASM 2 ingestion through PyZX."""

from __future__ import annotations

from pyzx import Circuit
from pyzx.circuit.gates import Measurement, Reset

from mini_zx_library.ingestion import SourceDocument, _ImportResult

_NON_UNITARY_GATE_TYPES = (Measurement, Reset)


class OpenQasm2Adapter:
    """Convert unitary OpenQASM 2 source into an unsimplified PyZX graph."""

    name = "openqasm2-pyzx"
    version = "1"

    def convert(self, source: SourceDocument) -> _ImportResult:
        """Parse unitary OpenQASM 2 and return its PyZX JSON graph."""
        try:
            text = source.content.decode("utf-8")
        except UnicodeDecodeError as error:
            message = "OpenQASM source must contain valid UTF-8"
            raise ValueError(message) from error

        try:
            circuit = Circuit.from_qasm(text)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            message = "OpenQASM source must contain supported OpenQASM 2"
            raise ValueError(message) from error

        for gate in circuit.gates:
            if isinstance(gate, _NON_UNITARY_GATE_TYPES):
                message = (
                    "OpenQASM source contains unsupported non-unitary operation "
                    f"{gate.name}"
                )
                raise ValueError(message)

        try:
            graph = circuit.to_graph()
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            message = "OpenQASM circuit could not be converted to a PyZX graph"
            raise ValueError(message) from error

        if not graph.is_well_formed():
            message = "OpenQASM conversion must produce a well-formed graph"
            raise ValueError(message)

        return _ImportResult(
            graph_format="pyzx-json-v2",
            graph_content=graph.to_json().encode("utf-8"),
        )
