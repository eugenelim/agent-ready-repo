"""Construction stubs for direct-source admission and normalization."""

from __future__ import annotations


def test_classification_contract():
    # STUB: AC1, AC2, AC14, AC15, AC16, AC17, AC25, AC32, AC33, AC34, AC35, AC36
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.classify_direct_source)


def test_normalization_projection_parity():
    # STUB: AC24, AC25
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.normalize_direct_source)


def test_bounded_metadata_characterization():
    # STUB: AC14, AC15, AC16, AC17, AC18, AC19, AC20
    import agentbundle.bounded_metadata as bounded_metadata

    assert callable(bounded_metadata.parse_bounded_metadata)


def test_direct_admission_diagnostic_registry():
    # STUB: AC9, AC11, AC14, AC15, AC16, AC17, AC18, AC19, AC20, AC21, AC25, AC27, AC34, AC39
    import agentbundle.direct_source as direct_source

    assert callable(direct_source.admit_direct_source)
