"""T3: config.py — _parse_adapter_row uses LEGAL_SCOPES for scope allowlist.

Verifies AC5: scope="local" rows are preserved; unknown scopes still coerce
to the default_scope fallback.
"""

from __future__ import annotations

from agentbundle.config import _parse_adapter_row


def test_parse_adapter_row_preserves_local_scope():
    """scope="local" in state row is preserved, not coerced."""
    body = {"scope": "local", "files": {}}
    row = _parse_adapter_row("mypkg", "claude-code", body, default_scope="repo")
    assert row.scope == "local"


def test_parse_adapter_row_coerces_unknown_scope():
    """An unknown scope value still coerces to the default_scope."""
    body = {"scope": "totally-unknown", "files": {}}
    row = _parse_adapter_row("mypkg", "claude-code", body, default_scope="repo")
    assert row.scope == "repo"


def test_parse_adapter_row_preserves_repo_scope():
    """Existing repo scope rows unaffected."""
    body = {"scope": "repo", "files": {}}
    row = _parse_adapter_row("mypkg", "claude-code", body, default_scope="user")
    assert row.scope == "repo"


def test_parse_adapter_row_preserves_user_scope():
    """Existing user scope rows unaffected."""
    body = {"scope": "user", "files": {}}
    row = _parse_adapter_row("mypkg", "claude-code", body, default_scope="repo")
    assert row.scope == "user"
