"""T18: every write-capable subcommand refuses against a v0.1 state file.

Verifies AC #(RFC-0004) for the agent-spec-cli spec:
  - install, uninstall, upgrade, init-state (without --migrate) refuse on
    a v0.1 .agentbundle-state.toml with the documented stderr.
  - Read-only subcommands (list-targets, diff, adapt without
    --values-from) succeed against the same v0.1 fixture, treating every
    pack entry as repo-scope.

Parametrisation: each write-capable subcommand is exercised by calling
its handler directly with a minimal argparse.Namespace. We stage a
v0.1 state file at the repo root before the call.
"""

from __future__ import annotations

import contextlib
import io
import argparse
from pathlib import Path

import pytest

from agentbundle.commands import install, uninstall, upgrade, init_state, adapt, diff


V01_STATE = """
schema-version = "0.1"

[pack.core]
installed-version = "0.1.0"
source = "agent-ready-repo"
install-route = "cli"
primitives = ["skill"]

[pack.core.files]
"AGENTS.md" = { sha = "00", from-pack-version = "0.1.0" }
"""


def _v01(tmp_path: Path) -> Path:
    p = tmp_path / ".agentbundle-state.toml"
    p.write_text(V01_STATE, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Write-capable subcommands refuse on v0.1
# ---------------------------------------------------------------------------


def _assert_refused(rc: int, stderr: str, verb: str) -> None:
    assert rc != 0, f"{verb} accepted a v0.1 state file"
    assert "schema-version 0.1" in stderr, (
        f"{verb} stderr missing 'schema-version 0.1': {stderr!r}"
    )
    # Greenfield (RFC-0052 D8): the refusal directs re-install, not --migrate.
    assert "reinstall" in stderr.lower(), (
        f"{verb} stderr missing reinstall hint: {stderr!r}"
    )


def test_install_refuses_v01_state(tmp_path):
    _v01(tmp_path)
    # Stage a local catalogue with a minimal pack so install reaches the
    # state-load step before any other failure.
    pack = tmp_path / "catalogue" / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (pack / ".apm").mkdir()  # empty apm so render is a no-op

    args = argparse.Namespace(
        pack="demo",
        catalogue=str(tmp_path / "catalogue"),
        output=str(tmp_path),
        scope=None,
        force=False,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = install.run(args)
    _assert_refused(rc, buf.getvalue(), "install")


def test_uninstall_refuses_v01_state(tmp_path):
    _v01(tmp_path)
    args = argparse.Namespace(pack="core", root=str(tmp_path), scope=None)
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = uninstall.run(args)
    _assert_refused(rc, buf.getvalue(), "uninstall")


def test_upgrade_refuses_v01_state(tmp_path):
    _v01(tmp_path)
    pack = tmp_path / "catalogue" / "core"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    (pack / ".apm").mkdir()
    args = argparse.Namespace(
        pack="core",
        catalogue=str(tmp_path / "catalogue"),
        yes=True,
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        root=str(tmp_path),
        scope=None,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = upgrade.run(args)
    _assert_refused(rc, buf.getvalue(), "upgrade")


def test_init_state_without_migrate_refuses_v01(tmp_path):
    _v01(tmp_path)
    pack = tmp_path / "packs" / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    args = argparse.Namespace(
        pack="demo",
        packs_dir=str(tmp_path / "packs"),
        root=str(tmp_path),
        migrate=False,
        scope=None,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = init_state.run(args)
    _assert_refused(rc, buf.getvalue(), "init-state")


# ---------------------------------------------------------------------------
# Read-only subcommands ALSO refuse a legacy file under v0.4 (RFC-0052):
# the hard cross-version refusal fires on read, not just write. They must
# refuse *gracefully* (clean stderr + non-zero), never traceback.
# ---------------------------------------------------------------------------


def test_adapt_ci_refuses_legacy_state_gracefully(tmp_path):
    """adapt --ci reads state; a legacy file refuses with a clean message."""
    _v01(tmp_path)
    args = argparse.Namespace(values_from=None, ci=True, root=str(tmp_path))
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = adapt.run(args)
    assert rc == 1
    assert "schema-version 0.1" in buf.getvalue()


def test_diff_refuses_legacy_state_gracefully(tmp_path):
    """diff reads state for its shape detection; a legacy file refuses
    with a clean message rather than tracebacking."""
    _v01(tmp_path)
    pack = tmp_path / "packs" / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    args = argparse.Namespace(
        pack_path=str(pack), root=str(tmp_path), scope=None, adapter=None
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        try:
            rc = diff.run(args)
        except Exception as exc:  # pragma: no cover — surfaces a regression
            pytest.fail(f"diff tracebacked on a legacy state file: {exc!r}")
    assert rc == 1
    assert "schema-version 0.1" in buf.getvalue()
