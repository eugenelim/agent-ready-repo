"""T4: _common.py — resolve_state_path handles 'local' scope.

Verifies AC6: resolve_state_path("local", root) returns
root / ".agentbundle-local-state.toml".
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.commands._common import resolve_state_path


def test_resolve_state_path_local():
    """Local scope → .agentbundle-local-state.toml in repo root."""
    root = Path("/repo")
    assert resolve_state_path("local", root) == Path("/repo/.agentbundle-local-state.toml")


def test_resolve_state_path_repo_unchanged():
    """Existing repo scope routing unaffected."""
    root = Path("/repo")
    assert resolve_state_path("repo", root) == Path("/repo/.agentbundle-state.toml")


def test_resolve_state_path_user_unchanged(tmp_path):
    """Existing user scope routing unaffected."""
    assert resolve_state_path("user", tmp_path) == tmp_path / ".agentbundle" / "state.toml"
