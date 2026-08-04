"""Tests for permissions.allow projection via agentbundle install core.

AC17/AC18 are deferred (workspace-mcp-permissions-projection-contract).

Deferral reason: the current adapter contract's merge-json mode handles
dict payloads; permissions.allow is an array. Additive array merging
requires a new adapter projection mode and schema bump — follow-on RFC.

When the follow-on RFC ships, implement these stubs.
"""
import pytest


class TestPermissionsAllowProjection:
    """AC17: agentbundle install core adds 6 mcp__workspace-mcp__* entries."""

    def test_install_core_adds_six_permission_entries(self) -> None:
        assert False  # STUB: AC17 (deferred) — install core on clean tmp repo; parse .claude/settings.json; assert all 6 ids in permissions.allow

    def test_install_core_preserves_existing_entries(self) -> None:
        assert False  # STUB: AC18 (deferred) — pre-populate permissions.allow; install core; assert existing entries still present

    def test_install_core_does_not_duplicate_entries(self) -> None:
        assert False  # STUB: AC18 (deferred) — install core twice; assert no duplicate entries in permissions.allow

    def test_install_core_does_not_clobber_other_keys(self) -> None:
        assert False  # STUB: AC18 (deferred) — pre-populate unrelated settings.json key; install core; assert key preserved
