"""Shared construction boundary for derived graph artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mini_zx_library.model import (
    DerivedGraphArtifact,
    GraphRepresentation,
    RawGraphArtifact,
    Transformation,
    sha256_bytes,
)


@dataclass(frozen=True, slots=True)
class _TransformationResult:
    """Internal source-independent output produced by a graph transformer."""

    graph_format: str
    graph_content: bytes


@dataclass(frozen=True, slots=True)
class DerivedGraphResult:
    """A derived artifact paired with its serialized graph content."""

    artifact: DerivedGraphArtifact
    graph_content: bytes


class GraphTransformer(Protocol):
    """Structural interface implemented by graph transformations."""

    name: str
    version: str
    parameters: tuple[tuple[str, str], ...]

    def transform(self, graph_content: bytes) -> _TransformationResult:
        """Transform serialized graph content without constructing an artifact."""
        ...


class GraphDigestMismatchError(ValueError):
    """Raised when supplied graph content does not match its parent artifact."""


class DerivationBuilder:
    """Apply shared hashing and lineage policy to transformed graph output."""

    def build(
        self,
        parent: RawGraphArtifact | DerivedGraphArtifact,
        parent_graph_content: bytes,
        transformer: GraphTransformer,
    ) -> DerivedGraphResult:
        """Transform verified parent content and construct its derived artifact."""
        if sha256_bytes(parent_graph_content) != parent.graph.graph_sha256:
            message = "parent graph content does not match its recorded digest"
            raise GraphDigestMismatchError(message)

        result = transformer.transform(parent_graph_content)
        transformation = Transformation(
            name=transformer.name,
            version=transformer.version,
            parameters=transformer.parameters,
        )
        graph = GraphRepresentation(
            format=result.graph_format,
            graph_sha256=sha256_bytes(result.graph_content),
        )
        artifact = DerivedGraphArtifact(
            parent_id=parent.artifact_id,
            transformation=transformation,
            graph=graph,
        )

        return DerivedGraphResult(
            artifact=artifact,
            graph_content=result.graph_content,
        )
