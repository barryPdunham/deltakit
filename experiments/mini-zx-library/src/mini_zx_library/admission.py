"""Source-independent corpus admission policy."""

from __future__ import annotations

from mini_zx_library.model import DistributionMode, SourceProvenance


class ProvenanceAdmissionError(ValueError):
    """Raised when provenance does not satisfy corpus admission policy."""


def require_admissible_provenance(provenance: SourceProvenance) -> None:
    """Require provenance to satisfy the corpus's minimum admission rule."""
    if (
        provenance.license_expression == "NOASSERTION"
        and provenance.distribution_mode is not DistributionMode.REFERENCE_ONLY
    ):
        message = "Provenance with NOASSERTION must use reference-only distribution"
        raise ProvenanceAdmissionError(message)
