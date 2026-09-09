"""Shared ingestion boundary for source-specific adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mini_zx_library.admission import require_admissible_provenance
from mini_zx_library.model import (
    GraphRepresentation,
    QecSidecar,
    RawGraphArtifact,
    SourceIdentity,
    SourceProvenance,
    sha256_bytes,
)


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Exact upstream source content and its stable location."""

    collection: str
    entry_id: str
    revision: str
    provenance: SourceProvenance
    content: bytes


@dataclass(frozen=True, slots=True)
class _ImportResult:
    """Internal source-independent result produced by an adapter."""

    graph_format: str
    graph_content: bytes
    qec: QecSidecar | None = None


class SourceAdapter(Protocol):
    """Structural interface implemented by source-specific adapters."""

    name: str
    version: str

    def convert(self, source: SourceDocument) -> _ImportResult:
        """Convert one source document without constructing its artifact."""
        ...


class CorpusBuilder:
    """Apply shared identity and hashing policy to adapter output."""

    def build(
        self,
        source: SourceDocument,
        adapter: SourceAdapter,
    ) -> RawGraphArtifact:
        """Convert a source and construct its immutable raw artifact."""
        require_admissible_provenance(source.provenance)
        result = adapter.convert(source)

        source_identity = SourceIdentity(
            collection=source.collection,
            entry_id=source.entry_id,
            revision=source.revision,
            source_sha256=sha256_bytes(source.content),
            adapter_name=adapter.name,
            adapter_version=adapter.version,
        )
        graph = GraphRepresentation(
            format=result.graph_format,
            graph_sha256=sha256_bytes(result.graph_content),
        )

        return RawGraphArtifact(
            source=source_identity,
            graph=graph,
            provenance=source.provenance,
            qec=result.qec,
        )
