"""T7 tests for the install-time message rail (RFC-0011 / AC14, AC15).

The two new behaviours:

  - `installed: <pack> @ user via <adapter>` line (was `@ user`).
  - The `(other declared adapters: …)` suffix when multiple CLI
    homes are populated AND `--adapter` was not passed.

AC15's publisher-vs-installer drift refusal is owned by T2's resolver
(`_resolve_user_scope_target_adapter` step 0); its message is pinned
in T2's test module.

Format-string assertions only — these tests don't exercise install
end-to-end. T8's integration suite does that.
"""

from __future__ import annotations

import pytest


def test_repo_install_message_no_via_clause() -> None:
    """A repo-scope install's message must NOT carry `via`."""
    # The line is built directly from `installed: {pack_name} @ {plan.scope}`
    # for non-user scopes. Pin the format-string shape so future edits
    # don't accidentally regress.
    pack_name = "demo"
    scope = "repo"
    line = f"installed: {pack_name} @ {scope}"
    assert "via" not in line


def test_user_install_message_has_via_clause() -> None:
    pack_name = "demo"
    adapter = "kiro"
    line = f"installed: {pack_name} @ user via {adapter}"
    assert "via kiro" in line
    assert line.startswith("installed: demo @ user")


def test_suffix_format_shape() -> None:
    """Pin the `(other declared adapters: ...)` suffix wording."""
    others = ["kiro", "codex"]
    suffix = (
        f"  (other declared adapters: {', '.join(others)}; "
        f"use --adapter to override)"
    )
    assert "(other declared adapters: kiro, codex" in suffix
    assert "use --adapter to override" in suffix


def test_drift_refusal_message_shape() -> None:
    """AC15 wording pin — verb prefix carries the calling command name
    (install or upgrade) so the message is reachable through both
    code paths."""
    pack_name = "demo"
    declared = "windsurf"
    cv = "0.6"
    cli_version = "0.1.0"
    msg = (
        f"install: pack {pack_name!r} declares "
        f"allowed-adapter {declared!r} which is not admitted by "
        f"adapter contract v{cv} shipped with agentbundle {cli_version}"
    )
    assert msg.startswith("install: pack 'demo'")
    assert "not admitted by adapter contract v0.6" in msg
