"""CLI-hygiene AC10–AC14: `install` of an already-installed pack offers to
`upgrade` instead of the old flat "use 'upgrade'" refusal.

  - TTY + 'y' → runs the whole-pack upgrade against the same catalogue/scope.
  - --yes → runs the upgrade without prompting.
  - non-TTY without --yes → keeps the historical refusal (CI contract).
  - --dry-run → keeps the historical refusal (no offer, no prompt).

The handoff namespace (`_offer_upgrade`) is asserted to carry the full attribute
set `upgrade.run` reads, with the concrete resolved scope and whole-pack flags.
"""

from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path

import pytest

FIXTURE_CATALOGUE = (
    Path(__file__).parent.parent / "fixtures" / "install" / "catalogue"
)


def _install_args(output: str, **overrides) -> argparse.Namespace:
    base = dict(
        pack="alpha",
        catalogue=str(FIXTURE_CATALOGUE),
        output=output,
        scope=None,
        force=False,
        force_merge=False,
        dry_run=False,
        yes=False,
        adapter=None,
        emit_install_routes=True,  # dist-tree shape (fixture predates per-IDE)
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _run_install(args: argparse.Namespace) -> tuple[int, str, str]:
    from agentbundle.commands.install import run

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = run(args)
    return rc, out.getvalue(), err.getvalue()


def _install_alpha(tmp_path: Path) -> None:
    rc, _, err = _run_install(_install_args(str(tmp_path)))
    assert rc == 0, f"initial install failed: {err}"


def test_offer_accept_runs_upgrade_with_full_handoff(tmp_path, monkeypatch):
    """AC11: a TTY 'y' hands off to upgrade.run with the full, concrete namespace."""
    _install_alpha(tmp_path)

    captured = {}

    def _fake_upgrade(ns):
        captured["ns"] = ns
        return 0

    monkeypatch.setattr("agentbundle.commands.upgrade.run", _fake_upgrade)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    rc, _out, _err = _run_install(_install_args(str(tmp_path)))
    assert rc == 0
    ns = captured["ns"]
    assert ns.pack == "alpha"
    assert ns.catalogue == str(FIXTURE_CATALOGUE)
    assert ns.root == str(tmp_path)
    assert ns.scope == "repo", "handoff must pass the concrete resolved scope, not None"
    assert ns.yes is True
    assert ns.dry_run is False
    assert ns.skill is ns.agent is ns.hook is ns.seed is ns.command is None
    assert hasattr(ns, "_user_config")


def test_yes_runs_upgrade_without_prompting(tmp_path, monkeypatch):
    """AC12: install --yes of an already-installed pack runs upgrade, no prompt."""
    _install_alpha(tmp_path)

    captured = {}

    def _fake_upgrade(ns):
        captured["ns"] = ns
        return 0

    def _boom(prompt=""):
        raise AssertionError("input() must not be called with --yes")

    monkeypatch.setattr("agentbundle.commands.upgrade.run", _fake_upgrade)
    monkeypatch.setattr("builtins.input", _boom)

    rc, _out, _err = _run_install(_install_args(str(tmp_path), yes=True))
    assert rc == 0
    assert captured["ns"].yes is True


def test_non_tty_without_yes_keeps_refusal(tmp_path, monkeypatch):
    """AC13: a non-TTY without --yes keeps the historical refusal (no upgrade)."""
    _install_alpha(tmp_path)

    def _fake_upgrade(ns):
        raise AssertionError("upgrade.run must not be called on the refusal path")

    monkeypatch.setattr("agentbundle.commands.upgrade.run", _fake_upgrade)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    rc, _out, err = _run_install(_install_args(str(tmp_path)))
    assert rc == 1
    assert "already installed at repo" in err
    assert "use 'upgrade' to change version" in err


def test_dry_run_keeps_refusal_no_offer(tmp_path, monkeypatch):
    """AC13: install --dry-run of an already-installed pack refuses, no prompt."""
    _install_alpha(tmp_path)

    def _fake_upgrade(ns):
        raise AssertionError("upgrade.run must not be called under --dry-run")

    def _boom(prompt=""):
        raise AssertionError("input() must not be called under --dry-run")

    monkeypatch.setattr("agentbundle.commands.upgrade.run", _fake_upgrade)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _boom)

    # dry-run + force is mutex, so dry-run alone (force=False) here.
    rc, _out, err = _run_install(_install_args(str(tmp_path), dry_run=True))
    assert rc == 1
    assert "use 'upgrade' to change version" in err


def test_yes_runs_real_upgrade_end_to_end(tmp_path):
    """AC12 (real wiring): install --yes of an already-installed pack actually
    drives upgrade.run (no monkeypatch) and exits 0 with the upgrade recap."""
    _install_alpha(tmp_path)
    rc, out, err = _run_install(_install_args(str(tmp_path), yes=True))
    assert rc == 0, f"real upgrade handoff failed: {err}"
    # upgrade prints an `upgraded: <pack> @ <scope> <from> -> <to>` recap —
    # assert the specific recap so a silent no-op / error can't pass.
    assert "upgraded: alpha @ repo" in out, f"missing upgrade recap; stdout={out!r}"
