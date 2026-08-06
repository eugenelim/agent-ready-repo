"""T2: scope.py — extend LEGAL_SCOPES and resolve() guard for local scope.

Verifies AC2 (LEGAL_SCOPES), AC3 (default-scope=local refusal),
AC4 (D4 auto-promote: local permitted when repo is in allowed-scopes).
"""

from __future__ import annotations

import pytest
from agentbundle import scope

# ---------------------------------------------------------------------------
# LEGAL_SCOPES includes "local"
# ---------------------------------------------------------------------------


def test_legal_scopes_contains_local():
    """LEGAL_SCOPES must equal {"repo", "user", "local"}."""
    assert frozenset({"repo", "user", "local"}) == scope.LEGAL_SCOPES


# ---------------------------------------------------------------------------
# D4 auto-promote — local permitted when repo is in allowed-scopes
# ---------------------------------------------------------------------------


def test_resolve_local_when_repo_in_allowed():
    """resolve(requested='local', allowed=['repo']) → 'local'.

    The D4 auto-promote rule: "local" is not required to appear in
    allowed-scopes; the presence of "repo" is sufficient.
    """
    install = {"default-scope": "repo", "allowed-scopes": ["repo"]}
    assert scope.resolve("local", install) == "local"


def test_resolve_local_refused_when_repo_not_in_allowed():
    """AC4 negative: resolve(requested='local', allowed=['user']) raises ScopeRefused.

    "user" alone in allowed-scopes does not grant local-scope access.
    """
    install = {"default-scope": "user", "allowed-scopes": ["user"]}
    with pytest.raises(scope.ScopeRefused):
        scope.resolve("local", install)


# ---------------------------------------------------------------------------
# default-scope="local" in pack manifest raises ScopeRefused
# ---------------------------------------------------------------------------


def test_resolve_refuses_local_as_default_scope():
    """If the pack's default-scope resolves to "local", raise ScopeRefused.

    packs are not permitted to declare default-scope = "local" (schema
    also disallows it, but runtime guard is defense-in-depth).
    The refusal fires before the D4 auto-promote logic.
    """
    # Construct a pack_install where default-scope is "local".
    # Normally the schema would block this, but runtime must also guard.
    install = {"default-scope": "local", "allowed-scopes": ["repo", "local"]}
    # requested=None → resolved default ("local") triggers the guard
    with pytest.raises(scope.ScopeRefused):
        scope.resolve(None, install)
