"""In-memory registry for immutable ZX-graph artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum

from mini_zx_library.model import DerivedGraphArtifact, RawGraphArtifact

Artifact = RawGraphArtifact | DerivedGraphArtifact


class ArtifactKind(Enum):
    """Kinds of artifacts stored in the registry."""

    RAW = "raw"
    DERIVED = "derived"


class ArtifactConflictError(ValueError):
    """Raised when one artifact ID refers to unequal records."""


class ArtifactNotFoundError(LookupError):
    """Raised when an artifact ID is absent from the registry."""


class ArtifactRegistry:
    """Store and retrieve immutable raw and derived artifacts."""

    def __init__(self, artifacts: Iterable[Artifact] = ()) -> None:
        self._artifacts: dict[str, Artifact] = {}
        for artifact in artifacts:
            self.register(artifact)

    def __len__(self) -> int:
        return len(self._artifacts)

    def register(self, artifact: Artifact) -> None:
        """Register an artifact, treating an identical repeat as a no-op."""
        existing = self._artifacts.get(artifact.artifact_id)

        if existing is None:
            self._artifacts[artifact.artifact_id] = artifact
            return

        if existing != artifact:
            message = "artifact identity conflict: equal IDs refer to unequal records"
            raise ArtifactConflictError(message)

    def get(self, artifact_id: str) -> Artifact:
        """Retrieve one artifact by its deterministic identity."""
        try:
            return self._artifacts[artifact_id]
        except KeyError as error:
            message = f"artifact not found: {artifact_id}"
            raise ArtifactNotFoundError(message) from error

    def get_many(self, artifact_ids: Iterable[str]) -> tuple[Artifact, ...]:
        """Retrieve artifacts in the order requested by the caller."""
        return tuple(self.get(artifact_id) for artifact_id in artifact_ids)

    def all(self) -> tuple[Artifact, ...]:
        """Return every artifact in deterministic identity order."""
        return tuple(
            self._artifacts[artifact_id] for artifact_id in sorted(self._artifacts)
        )

    def select(
        self,
        *,
        kind: ArtifactKind | None = None,
        collection: str | None = None,
        has_qec: bool | None = None,
    ) -> tuple[Artifact, ...]:
        """Return artifacts matching all supplied filters."""
        selected: list[Artifact] = []

        for artifact in self.all():
            if kind is not None and _artifact_kind(artifact) is not kind:
                continue
            if collection is not None and not _belongs_to_collection(
                artifact, collection
            ):
                continue
            if has_qec is not None and _has_qec_sidecar(artifact) is not has_qec:
                continue
            selected.append(artifact)

        return tuple(selected)


def _artifact_kind(artifact: Artifact) -> ArtifactKind:
    if isinstance(artifact, RawGraphArtifact):
        return ArtifactKind.RAW
    return ArtifactKind.DERIVED


def _belongs_to_collection(
    artifact: Artifact,
    collection: str,
) -> bool:
    return (
        isinstance(artifact, RawGraphArtifact)
        and artifact.source.collection == collection
    )


def _has_qec_sidecar(artifact: Artifact) -> bool:
    return isinstance(artifact, RawGraphArtifact) and artifact.qec is not None
