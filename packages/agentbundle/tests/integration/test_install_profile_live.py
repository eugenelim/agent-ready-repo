"""T6 (pack-profiles AC14): the two shipped profiles install cleanly against
the live catalogue (the repo root) into temp scope roots.

Goal-based smoke: `full-ceremony` (repo) and `solution-architect` (user) each
install end-to-end with default adapter resolution, every pack landing at the
declared scope with `install_route="profile"`. This is the real-artifact
exercise the work-loop requires for a user-invoked CLI feature.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest

# repo root: packages/agentbundle/tests/integration/<file> → parents[4].
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(autouse=True)
def _isolate_home_and_caches(tmp_path, monkeypatch):
    from agentbundle.commands import install

    home = tmp_path / "iso_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()
    yield
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()


def _run_install(argv):
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install
    from agentbundle.user_config import load_user_config

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    args._user_config = load_user_config()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def test_full_ceremony_installs_at_repo_scope(tmp_path):
    from agentbundle.config import load_state

    target = tmp_path / "repo"
    target.mkdir()
    rc, out, err = _run_install(
        ["--profile", "full-ceremony", str(REPO_ROOT), "--output", str(target)]
    )
    assert rc == 0, f"full-ceremony install failed: {err}"

    state = load_state(target / ".agentbundle-state.toml")
    for name in ("core", "governance-extras", "user-guide-diataxis", "monorepo-extras"):
        assert name in state.packs, f"{name} missing; summary:\n{out}\nstderr:\n{err}"
        assert state.packs[name].install_route == "profile"
        assert state.packs[name].scope == "repo"


def test_solution_architect_installs_at_user_scope(tmp_path, monkeypatch):
    from agentbundle import scope as scope_mod
    from agentbundle.config import load_state

    # User-scope install writes under $HOME (isolated by the autouse fixture);
    # --output is irrelevant to user scope but pinned to tmp so a future
    # output-resolution change can't scribble into the working tree.
    rc, out, err = _run_install(
        ["--profile", "solution-architect", str(REPO_ROOT), "--output", str(tmp_path)]
    )
    assert rc == 0, f"solution-architect install failed: {err}"

    user_root = scope_mod.resolve_user_root()
    state = load_state(user_root / ".agentbundle" / "state.toml")
    for name in ("architect", "research", "contracts"):
        assert name in state.packs, f"{name} missing; summary:\n{out}\nstderr:\n{err}"
        assert state.packs[name].install_route == "profile"
        assert state.packs[name].scope == "user"
