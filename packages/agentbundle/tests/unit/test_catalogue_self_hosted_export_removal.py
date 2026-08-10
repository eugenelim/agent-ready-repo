"""Verify the reusable catalogue identity module's package placement."""

from __future__ import annotations

from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Identity module presence (replacement landed correctly)
# ---------------------------------------------------------------------------

def test_identity_module_present() -> None:
    identity_module = _PACKAGE_ROOT / "agentbundle" / "catalogue_tooling" / "identity.py"
    assert identity_module.exists(), "identity.py migration target not found"


def test_identity_module_exports_expected_symbols() -> None:
    from agentbundle.catalogue_tooling.identity import (
        BINARY_EXT,
        check_ci_boundary,
        verify,
    )
    assert callable(verify)
    assert callable(check_ci_boundary)
    assert isinstance(BINARY_EXT, frozenset)
