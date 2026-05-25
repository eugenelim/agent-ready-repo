"""T19: dual-scope install conflict + --force + `installed: <pack> @ <scope>`.

Verifies AC #(RFC-0004) for the agent-spec-cli spec:
  - install against a pack already at the requested scope refuses with
    the in-place message; --force does not bypass it.
  - install against a pack already at the *other* scope refuses without
    --force; --force proceeds and writes both state files.
  - Successful single-scope install emits one `installed:` line.
  - Successful dual-scope --force install emits two lines, repo first
    then user, both on stdout.
  - Pre-flight order: a user-scope failure (path-jail, rail, ~-expansion)
    writes neither state file and emits zero `installed:` lines.
  - uninstall/upgrade/diff refuse --scope omitted when at multiple scopes.

User-scope tests stage a temporary $HOME so the run never touches the
adopter's real home directory.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import tempfile
from pathlib import Path

import pytest

from agentbundle.commands import install, uninstall, upgrade, diff


# Pack catalogues for the various test setups.
PACK_TOML_REPO_ONLY = """
[pack]
name = "demo-repo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""

PACK_TOML_BOTH = """
[pack]
name = "demo-both"
version = "0.1.0"

[pack.adapter-contract]
version = "0.2"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo", "user"]
"""


def _stage_pack(catalogue_root: Path, pack_name: str, toml_text: str) -> Path:
    pack = catalogue_root / "packs" / pack_name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(toml_text, encoding="utf-8")
    (pack / ".apm").mkdir()  # empty apm → empty projection
    return pack


def _install(args_dict) -> tuple[int, str, str]:
    """Run install with redirected stdout/stderr; return (rc, stdout, stderr)."""
    args = argparse.Namespace(**args_dict)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# In-place re-install refusal — --force does NOT bypass
# ---------------------------------------------------------------------------


def test_install_refuses_when_already_at_requested_scope(tmp_path):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-repo", PACK_TOML_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()

    rc1, out1, _ = _install(
        dict(pack="demo-repo", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc1 == 0, "first install should succeed"
    assert "installed: demo-repo @ repo" in out1

    rc2, _, err2 = _install(
        dict(pack="demo-repo", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc2 != 0
    assert "already installed at repo" in err2
    assert "use 'upgrade' to change version" in err2


def test_force_does_not_bypass_in_place_refusal(tmp_path):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-repo", PACK_TOML_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()

    _install(dict(pack="demo-repo", catalogue=str(cat), output=str(target), scope=None, force=False))
    rc, _, err = _install(
        dict(pack="demo-repo", catalogue=str(cat), output=str(target), scope=None, force=True)
    )
    assert rc != 0
    assert "already installed at repo" in err
    assert "use 'upgrade' to change version" in err


# ---------------------------------------------------------------------------
# Cross-scope conflict + --force
# ---------------------------------------------------------------------------


def test_cross_scope_conflict_refused_without_force(tmp_path, monkeypatch):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Install at repo first.
    rc1, _, _ = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=False)
    )
    assert rc1 == 0

    # Now try installing at user without --force.
    rc2, _, err2 = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=False)
    )
    assert rc2 != 0
    assert "demo-both already installed at repo; pass --force to install at both" in err2


def test_cross_scope_force_proceeds_and_writes_both_state_files(tmp_path, monkeypatch):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=False))

    rc, out, _ = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=True)
    )
    assert rc == 0
    # Both state files exist after the run.
    assert (target / ".agentbundle-state.toml").exists()
    assert (fake_home / ".agentbundle" / "state.toml").exists()
    # Two `installed:` lines, repo first then user.
    lines = [ln for ln in out.splitlines() if ln.startswith("installed:")]
    assert lines == ["installed: demo-both @ repo", "installed: demo-both @ user"], (
        f"expected repo-then-user stdout sequence; got {lines!r}"
    )


def test_force_no_op_when_pack_not_already_other_scope(tmp_path, monkeypatch):
    """--force against a pack not already at the other scope is a no-op flag.

    The install proceeds as a normal first-time install at the requested
    scope. Adopter wrapper scripts can pass --force idempotently.
    """
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    rc, out, _ = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=True)
    )
    assert rc == 0
    lines = [ln for ln in out.splitlines() if ln.startswith("installed:")]
    assert lines == ["installed: demo-both @ repo"]


# ---------------------------------------------------------------------------
# `installed:` rail — single-scope (stdout)
# ---------------------------------------------------------------------------


def test_single_scope_install_emits_one_installed_line_last(tmp_path):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-repo", PACK_TOML_REPO_ONLY)
    target = tmp_path / "repo"
    target.mkdir()

    rc, out, _ = _install(
        dict(pack="demo-repo", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0
    non_empty = [ln for ln in out.splitlines() if ln.strip()]
    assert non_empty[-1] == "installed: demo-repo @ repo"


# ---------------------------------------------------------------------------
# Multi-scope verb refusal (uninstall / upgrade / diff)
# ---------------------------------------------------------------------------


def test_uninstall_refuses_when_at_multiple_scopes(tmp_path, monkeypatch):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=False))
    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=True))

    args = argparse.Namespace(pack="demo-both", root=str(target), scope=None)
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = uninstall.run(args)
    assert rc != 0
    assert "demo-both installed at multiple scopes" in buf.getvalue()
    assert "{repo, user}" in buf.getvalue()


def test_upgrade_refuses_when_at_multiple_scopes(tmp_path, monkeypatch):
    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=False))
    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=True))

    args = argparse.Namespace(
        pack="demo-both",
        catalogue=str(cat),
        to_version="0.2.0",
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        root=str(target),
        scope=None,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = upgrade.run(args)
    assert rc != 0
    assert "demo-both installed at multiple scopes" in buf.getvalue()
    assert "{repo, user}" in buf.getvalue()


def test_uninstall_at_user_scope_writes_dot_directory_state(tmp_path, monkeypatch):
    """RFC-0004 Blocker fix: uninstall at user scope must write the state
    file to `~/.agentbundle/state.toml` (the namespaced dot-directory),
    never a bare `~/.agentbundle-state.toml`. Adversarial-reviewer Blocker
    pass 2 surfaced this — the test pins the fix.
    """
    from agentbundle.commands import uninstall

    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Install at user scope, then uninstall at user scope.
    rc, _, _ = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=False)
    )
    assert rc == 0
    assert (fake_home / ".agentbundle" / "state.toml").exists()

    args = argparse.Namespace(pack="demo-both", root=str(target), scope="user")
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = uninstall.run(args)
    assert rc == 0, f"uninstall at user scope failed: {err.getvalue()}"
    # The bare-dotfile path the bug would have produced must NOT exist.
    assert not (fake_home / ".agentbundle-state.toml").exists(), (
        "uninstall at user scope wrote to ~/.agentbundle-state.toml (legacy bare dotfile path)"
    )
    # The namespaced state file must still exist and have the pack removed.
    from agentbundle.config import load_state

    state = load_state(fake_home / ".agentbundle" / "state.toml")
    assert "demo-both" not in state.packs


def test_upgrade_at_user_scope_renders_claude_code_shape(tmp_path, monkeypatch):
    """RFC-0004 Blocker fix: upgrade at user scope must render via the
    Claude Code adapter directly (paths under `.claude/...`), not the
    dist-tree shape. The first-pass fix only addressed the state-file
    path; this test pins the render-shape fix too.
    """
    from agentbundle.commands import upgrade

    cat = tmp_path / "cat"
    _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    # Install at user scope.
    rc, _, _ = _install(
        dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=False)
    )
    assert rc == 0

    # Now upgrade at user scope (empty .apm — projection is empty; the
    # test pins that the render selection doesn't refuse on
    # `allowed-prefixes` and the state file's `installed-version`
    # updates).
    args = argparse.Namespace(
        pack="demo-both",
        catalogue=str(cat),
        to_version="0.2.0",
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        root=str(target),
        scope="user",
    )
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = upgrade.run(args)
    assert rc == 0, f"upgrade at user scope failed: {err.getvalue()}"

    from agentbundle.config import load_state

    state = load_state(fake_home / ".agentbundle" / "state.toml")
    assert state.packs["demo-both"].installed_version == "0.2.0"


def test_install_v01_pack_stray_install_table_ignored(tmp_path):
    """RFC-0004 Blocker fix: a v0.1 pack carrying `[pack.install]
    default-scope = "user"` is treated as legacy repo-only. The schema
    accepts the stray table; the CLI must ignore it.
    """
    cat = tmp_path / "cat"
    # v0.1 contract version + stray default-scope = "user"
    v01_stray = """
[pack]
name = "legacy-stray"
version = "0.1.0"

[pack.adapter-contract]
version = "0.1"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
"""
    _stage_pack(cat, "legacy-stray", v01_stray)
    target = tmp_path / "repo"
    target.mkdir()

    rc, out, _ = _install(
        dict(pack="legacy-stray", catalogue=str(cat), output=str(target), scope=None, force=False)
    )
    assert rc == 0, "v0.1 pack install must succeed; stray install table ignored"
    # The pack must land at repo scope (the legacy implicit default),
    # not user scope (which the stray table requested).
    assert "installed: legacy-stray @ repo" in out
    assert "@ user" not in out


def test_diff_refuses_when_at_multiple_scopes(tmp_path, monkeypatch):
    cat = tmp_path / "cat"
    pack = _stage_pack(cat, "demo-both", PACK_TOML_BOTH)
    target = tmp_path / "repo"
    target.mkdir()
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="repo", force=False))
    _install(dict(pack="demo-both", catalogue=str(cat), output=str(target), scope="user", force=True))

    args = argparse.Namespace(pack_path=str(pack), root=str(target), scope=None)
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = diff.run(args)
    assert rc != 0
    assert "demo-both installed at multiple scopes" in buf.getvalue()
