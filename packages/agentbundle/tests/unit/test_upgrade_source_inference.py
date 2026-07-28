"""Unit tests for the source-inference fix in _run_source_version_preflight.

Covers the branch added in upgrade.py lines 218-228: when pack_state.source is
None (old installs that pre-date source recording), the function falls back to
the 5-layer default source resolution chain instead of immediately marking the
row as source-unknown/blocked.
"""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

from agentbundle.catalogue import CatalogueError
from agentbundle.commands.upgrade import _run_source_version_preflight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    pack_name: str = "my-pack", adapter: str = "claude-code", source=None, version: str = "0.1.0"
):
    """Build a minimal state namespace for _run_source_version_preflight."""
    pack_state = types.SimpleNamespace(
        installed_version=version,
        source=source,
    )
    return types.SimpleNamespace(packs={(pack_name, adapter): pack_state})


# ---------------------------------------------------------------------------
# Test 1: source=None → infer from default chain → row is NOT source-unknown
# ---------------------------------------------------------------------------


def test_source_none_infers_from_default_chain():
    """When source is None and the default chain succeeds, the row is not source-unknown.

    The inferred canonical source is set on the row; status_reason may be
    something like 'source-unavailable' (if resolve_catalogue fails) but must
    NOT be 'source-unknown' — that would mean inference was skipped.
    """
    state = _make_state(source=None)

    mock_resolve_cat = MagicMock(side_effect=CatalogueError("catalogue not found"))

    with (
        patch(
            "agentbundle.source_defaults.resolve_default_source",
            return_value="https://example.com/catalogue.toml",
        ),
        patch("agentbundle.commands.upgrade.resolve_catalogue", mock_resolve_cat),
    ):
        rows, _ = _run_source_version_preflight(state, scope="user", root=None)

    assert len(rows) == 1
    row = rows[0]
    assert row.canonical_source is not None, "canonical_source must be set when inference succeeds"
    assert row.status_reason != "source-unknown", (
        f"expected inference to succeed; got status_reason={row.status_reason!r}"
    )


# ---------------------------------------------------------------------------
# Test 2: source=None, default chain raises → row marked source-unknown
# ---------------------------------------------------------------------------


def test_source_none_default_chain_fails_marks_unknown():
    """When source is None and resolve_default_source raises CatalogueError,
    the row is marked status='unknown', status_reason='source-unknown'."""
    state = _make_state(source=None)

    with patch(
        "agentbundle.source_defaults.resolve_default_source",
        side_effect=CatalogueError("no default configured"),
    ):
        rows, _ = _run_source_version_preflight(state, scope="user", root=None)

    row = rows[0]
    assert row.status == "unknown"
    assert row.status_reason == "source-unknown"
    assert row.canonical_source is None


# ---------------------------------------------------------------------------
# Test 3: source is present → canonicalize_source called, resolve_default_source NOT called
# ---------------------------------------------------------------------------


def test_source_present_unchanged():
    """When pack_state.source is a real URL, resolve_default_source is never invoked.

    canonicalize_source normalizes the URL and passes it on to resolve_catalogue.
    """
    state = _make_state(source="https://example.com/foo.toml")

    mock_resolve_default = MagicMock()
    mock_resolve_cat = MagicMock(side_effect=CatalogueError("not found"))

    with (
        patch("agentbundle.source_defaults.resolve_default_source", mock_resolve_default),
        patch("agentbundle.commands.upgrade.resolve_catalogue", mock_resolve_cat),
    ):
        rows, _ = _run_source_version_preflight(state, scope="user", root=None)

    row = rows[0]
    # Default chain must NOT have been consulted
    mock_resolve_default.assert_not_called()
    # canonical_source must be derived from the pack's recorded source
    assert row.canonical_source is not None
    assert "example.com" in row.canonical_source


# ---------------------------------------------------------------------------
# Test 4: source="agent-ready-repo" (legacy sentinel) + default chain succeeds
# ---------------------------------------------------------------------------


def test_legacy_sentinel_source_infers_from_default_chain():
    """The legacy 'agent-ready-repo' sentinel is treated the same as None —
    inference via the 5-layer default chain, not an immediate source-unknown block.
    """
    state = _make_state(source="agent-ready-repo")

    mock_resolve_cat = MagicMock(side_effect=CatalogueError("catalogue not found"))

    with (
        patch(
            "agentbundle.source_defaults.resolve_default_source",
            return_value="https://example.com/catalogue.toml",
        ),
        patch("agentbundle.commands.upgrade.resolve_catalogue", mock_resolve_cat),
    ):
        rows, _ = _run_source_version_preflight(state, scope="user", root=None)

    row = rows[0]
    assert row.canonical_source is not None, "canonical_source must be set when inference succeeds"
    assert row.status_reason != "source-unknown", (
        f"expected inference to succeed; got status_reason={row.status_reason!r}"
    )


# ---------------------------------------------------------------------------
# Test 5: source="agent-ready-repo" (legacy sentinel) + default chain raises
# ---------------------------------------------------------------------------


def test_legacy_sentinel_source_default_chain_fails_marks_unknown():
    """When source is the legacy sentinel and resolve_default_source raises,
    the row is marked status='unknown', status_reason='source-unknown'."""
    state = _make_state(source="agent-ready-repo")

    with patch(
        "agentbundle.source_defaults.resolve_default_source",
        side_effect=CatalogueError("no default configured"),
    ):
        rows, _ = _run_source_version_preflight(state, scope="user", root=None)

    row = rows[0]
    assert row.status == "unknown"
    assert row.status_reason == "source-unknown"
    assert row.canonical_source is None
