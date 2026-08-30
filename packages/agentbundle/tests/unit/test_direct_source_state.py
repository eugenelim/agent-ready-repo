"""Construction stubs for direct-source lifecycle state."""

from __future__ import annotations


def test_digest_version_prefix_refuses():
    # STUB: AC12, AC13, AC22, AC26, AC28
    import agentbundle.direct_source_state as direct_source_state

    assert callable(direct_source_state.validate_direct_digest)


def test_interrupted_install_leaves_unowned_projection():
    # STUB: AC4, AC7, AC9, AC12, AC21, AC22, AC26, AC28, AC30, AC37, AC38
    import agentbundle.direct_source_state as direct_source_state

    assert callable(direct_source_state.record_direct_install)
