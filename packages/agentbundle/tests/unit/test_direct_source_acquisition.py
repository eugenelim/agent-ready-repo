"""Construction stubs for direct GitHub source acquisition."""

from __future__ import annotations


def test_git_https_acquisition_contract():
    # STUB: AC3, AC4, AC5, AC6, AC18, AC25, AC27, AC37
    import agentbundle.direct_source_acquisition as direct_source_acquisition

    assert callable(direct_source_acquisition.acquire_git_https_archive)
