"""Graph-native ingestion for PyZX version-2 JSON."""

from __future__ import annotations

import json

from pyzx.graph.base import BaseGraph

from mini_zx_library.ingestion import SourceDocument, _ImportResult

_PYZX_JSON_VERSION = 2


class PyZXJsonAdapter:
    """Validate graph-native PyZX JSON while preserving its exact source bytes."""

    name = "pyzx-json"
    version = "1"

    def convert(self, source: SourceDocument) -> _ImportResult:
        """Validate and return an existing PyZX JSON representation."""
        try:
            text = source.content.decode("utf-8")
        except UnicodeDecodeError as error:
            message = "PyZX JSON source must contain valid UTF-8"
            raise ValueError(message) from error

        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            message = "PyZX JSON source must contain valid JSON"
            raise ValueError(message) from error

        if not isinstance(document, dict):
            message = "PyZX JSON source must contain a JSON object"
            raise ValueError(message)

        version = document.get("version")
        if type(version) is not int or version != _PYZX_JSON_VERSION:
            message = "PyZX JSON source must explicitly use serialization version 2"
            raise ValueError(message)

        try:
            graph = BaseGraph.from_json(text)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            message = "PyZX JSON source could not be parsed as a version 2 graph"
            raise ValueError(message) from error

        if not graph.is_well_formed():
            message = "PyZX JSON source must describe a well-formed graph"
            raise ValueError(message)

        return _ImportResult(
            graph_format="pyzx-json-v2",
            graph_content=source.content,
        )
