"""Deterministic transformations of PyZX version-2 JSON graphs."""

from __future__ import annotations

import json

import pyzx as zx
from pyzx.graph.base import BaseGraph

from mini_zx_library.derivation import _TransformationResult

_PYZX_JSON_VERSION = 2


class PyZXSpiderSimplifier:
    """Apply PyZX spider fusion without mutating serialized parent content."""

    name = "pyzx-spider-simp"
    version = "1"
    parameters: tuple[tuple[str, str], ...] = ()

    def transform(self, graph_content: bytes) -> _TransformationResult:
        """Apply spider simplification to a well-formed serialized graph."""
        try:
            text = graph_content.decode("utf-8")
        except UnicodeDecodeError as error:
            message = "parent content must contain valid UTF-8"
            raise ValueError(message) from error

        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            message = "parent content must contain valid JSON"
            raise ValueError(message) from error

        version = document.get("version") if isinstance(document, dict) else None
        if type(version) is not int or version != _PYZX_JSON_VERSION:
            message = "parent content must explicitly use PyZX JSON version 2"
            raise ValueError(message)

        try:
            graph = BaseGraph.from_json(text)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            message = "parent content could not be parsed as a PyZX graph"
            raise ValueError(message) from error

        if not graph.is_well_formed():
            message = "parent content must describe a well-formed PyZX graph"
            raise ValueError(message)

        zx.spider_simp(graph)

        if not graph.is_well_formed():
            message = "spider simplification must produce a well-formed graph"
            raise ValueError(message)

        return _TransformationResult(
            graph_format="pyzx-json-v2",
            graph_content=graph.to_json().encode("utf-8"),
        )
