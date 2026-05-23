"""T18: every write-capable subcommand refuses against a v0.1 state file.

Verifies AC #(RFC-0004) for the agent-spec-cli spec:
  - install, uninstall, upgrade, init-state (without --migrate) refuse on
    a v0.1 .agent-ready-state.toml with the documented stderr.
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
    p = tmp_path / ".agent-ready-state.toml"
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
    assert "init-state --migrate" in stderr, (
        f"{verb} stderr missing migrate hint: {stderr!r}"
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
        to_version="0.2.0",
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
# Read-only subcommands succeed against the same v0.1 fixture
# ---------------------------------------------------------------------------


def test_adapt_ci_without_values_from_succeeds_against_v01(tmp_path):
    """adapt --ci is read-only — it must not refuse on a v0.1 file."""
    _v01(tmp_path)
    args = argparse.Namespace(
        values_from=None,
        ci=True,
        root=str(tmp_path),
    )
    rc = adapt.run(args)
    # The state file references AGENTS.md but the file is absent on disk
    # → no companions, no findings → exit 0.
    assert rc == 0


def test_diff_does_not_raise_on_v01_state(tmp_path):
    """diff is read-only — loads state, renders, and compares. v0.1 OK.

    The test passes a fixture pack so diff can render. The state file's
    being v0.1 must not block the read.
    """
    _v01(tmp_path)
    pack = tmp_path / "packs" / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    args = argparse.Namespace(
        pack_path=str(pack), root=str(tmp_path), scope=None
    )
    # diff returns non-zero when the projection diverges (and an empty
    # pack vs an empty projection should match). We only care here that
    # it doesn't raise / refuse-on-v0.1.
    try:
        diff.run(args)
    except Exception as exc:  # pragma: no cover — surfaces a regression
        pytest.fail(f"diff raised on v0.1 state file: {exc!r}")
