"""Tests for corpus provenance admission policy."""

import pytest
from mini_zx_library import (
    ProvenanceAdmissionError,
    require_admissible_provenance,
)
from mini_zx_library.ingestion import (
    CorpusBuilder,
    SourceDocument,
    _ImportResult,
)
from mini_zx_library.model import DistributionMode, SourceProvenance


def _provenance(
    *,
    license_expression: str,
    distribution_mode: DistributionMode,
) -> SourceProvenance:
    """Construct provenance for an admission-policy test."""
    return SourceProvenance(
        upstream_url="https://example.com/source",
        source_path="artifacts/example",
        license_expression=license_expression,
        license_reference="https://example.com/licensing",
        distribution_mode=distribution_mode,
    )


@pytest.mark.parametrize(
    "distribution_mode",
    [
        DistributionMode.BUNDLED,
        DistributionMode.FETCHED,
    ],
)
def test_noassertion_rejects_acquisition_or_distribution(
    distribution_mode: DistributionMode,
) -> None:
    provenance = _provenance(
        license_expression="NOASSERTION",
        distribution_mode=distribution_mode,
    )

    with pytest.raises(
        ProvenanceAdmissionError,
        match=r"NOASSERTION.*reference-only",
    ):
        require_admissible_provenance(provenance)


def test_noassertion_allows_reference_only_record() -> None:
    provenance = _provenance(
        license_expression="NOASSERTION",
        distribution_mode=DistributionMode.REFERENCE_ONLY,
    )

    require_admissible_provenance(provenance)


@pytest.mark.parametrize("distribution_mode", list(DistributionMode))
def test_identified_license_passes_minimum_admission_gate(
    distribution_mode: DistributionMode,
) -> None:
    provenance = _provenance(
        license_expression="Apache-2.0",
        distribution_mode=distribution_mode,
    )

    require_admissible_provenance(provenance)


class _AdapterThatMustNotRun:
    """Fail if corpus admission invokes conversion for a rejected source."""

    name = "must-not-run"
    version = "1"

    def convert(self, source: SourceDocument) -> _ImportResult:
        del source
        message = "adapter ran before provenance admission"
        raise AssertionError(message)


def test_builder_applies_admission_before_adapter_conversion() -> None:
    source = SourceDocument(
        collection="uncertain",
        entry_id="example",
        revision="1",
        content=b"source",
        provenance=_provenance(
            license_expression="NOASSERTION",
            distribution_mode=DistributionMode.BUNDLED,
        ),
    )

    with pytest.raises(ProvenanceAdmissionError):
        CorpusBuilder().build(source, _AdapterThatMustNotRun())
