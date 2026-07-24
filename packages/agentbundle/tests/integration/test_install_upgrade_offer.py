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
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

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
    assert ns.adapter is None, "handoff must carry the install-side --adapter (None here)"
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
    # install→upgrade of an already-installed pack at the same version is a
    # re-apply, not a version change: the recap reads `re-applied: … (already
    # current)`, never `upgraded: X -> X` (install-state-visibility AC10).
    assert "re-applied: alpha @ repo" in out, f"missing re-apply recap; stdout={out!r}"


def test_install_run_forwards_resolved_adapter_when_multi_adapter_and_no_cli_adapter(
    tmp_path, monkeypatch
):
    """Regression: install.run() must pass user_target_adapter as resolved_adapter
    to _offer_upgrade when --adapter is omitted and the pack is already installed
    for multiple adapters at user scope.

    Without this, _offer_upgrade forwards ns.adapter=None, and upgrade's
    multi-adapter disambiguator fires ("pass --adapter to pick one") even though
    install already selected the right row via its auto-detection probe.
    """
    converters_src = REPO_ROOT / "packs" / "converters"
    if not converters_src.is_dir():
        pytest.skip("converters pack not present in this checkout")

    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)  # probe → claude-code

    agentbundle_dir = home / ".agentbundle"
    agentbundle_dir.mkdir()
    from agentbundle.config import PackState, State, dump_state

    cat = tmp_path / "catalogue"
    (cat / "packs").mkdir(parents=True)

    two_adapter_state = State(
        packs={
            ("converters", "claude-code"): PackState(
                installed_version="0.8.0", adapter="claude-code", scope="user",
                source=str(cat),
            ),
            ("converters", "codex"): PackState(
                installed_version="0.8.0", adapter="codex", scope="user",
                source=str(cat),
            ),
        }
    )
    (agentbundle_dir / "state.toml").write_text(
        dump_state(two_adapter_state), encoding="utf-8"
    )
    shutil.copytree(converters_src, cat / "packs" / "converters")
    (tmp_path / "repo").mkdir()

    captured: dict = {}

    def _spy_offer(*_args, **kwargs):
        captured.update(kwargs)
        return 0

    from agentbundle.commands import install as _install_mod

    monkeypatch.setattr(_install_mod, "_offer_upgrade", _spy_offer)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    with patch.dict(os.environ, {"HOME": str(home), "USERPROFILE": str(home)}):
        args = argparse.Namespace(
            pack="converters",
            catalogue=str(cat),
            output=str(tmp_path / "repo"),
            scope="user",
            force=False,
            force_merge=False,
            dry_run=False,
            yes=False,
            adapter=None,
            emit_install_routes=False,
        )
        rc = _install_mod.run(args)

    assert "resolved_adapter" in captured, (
        f"_offer_upgrade was not called with resolved_adapter; "
        f"install.run() may have exited before the offer (rc={rc})"
    )
    assert captured["resolved_adapter"] == "claude-code", (
        f"expected resolved_adapter='claude-code' (probe picks ~/.claude/), "
        f"got {captured['resolved_adapter']!r}"
    )
