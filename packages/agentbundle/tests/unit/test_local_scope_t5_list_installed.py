"""T5: list_installed.py — three-scope default + local branch.

Verifies:
  - Without --scope, all three scopes are iterated (repo, user, local).
  - --scope local shows rows with scope=local and the annotation.
  - No local rows silently routed to the user state file.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentbundle.commands import list_installed as li
from agentbundle.config import PackState, State, dump_state  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(name: str, adapter: str = "claude-code", scope: str = "repo") -> State:
    """Return a one-entry State for a (name, adapter) pack."""
    ps = PackState(installed_version="0.1.0", scope=scope, adapter=adapter, source="installed-state")
    return State(packs={(name, adapter): ps})


def _make_args(**kw) -> SimpleNamespace:
    base = {
        "catalogue": None,
        "root": ".",
        "scope": None,
        "no_check": True,
        "check_drift": False,
        "format": "table",
        "updates_only": False,
        "_user_config": None,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def _write_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Test: three-scope default
# ---------------------------------------------------------------------------


def test_list_installed_iterates_local_scope_by_default(tmp_path, capsys):
    """Without --scope, list-installed loads repo, user, AND local state."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Write a local-scope state file
    local_state_path = repo_root / ".agentbundle-local-state.toml"
    _write_state(local_state_path, _entry("my-pack", scope="local"))

    args = _make_args(root=str(repo_root), scope=None)

    from agentbundle.scope import UserScopeUnresolvable

    with patch(
        "agentbundle.scope.resolve_user_root",
        side_effect=UserScopeUnresolvable("no user scope in test"),
    ):
        rc = li.run(args)

    captured = capsys.readouterr()
    assert rc == 0
    assert "my-pack" in captured.out


def test_list_installed_local_scope_not_routed_to_user_state(tmp_path, capsys):
    """Local rows must NOT appear in the user state file lookup.

    This tests that the explicit three-way branch in list_installed.run()
    routes sc == "local" to the local state file, not to the user state.
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Write a local-scope state file only
    local_state_path = repo_root / ".agentbundle-local-state.toml"
    _write_state(local_state_path, _entry("local-pack", scope="local"))

    # Write a user state file with a different pack
    user_root = tmp_path / "user"
    user_root.mkdir()
    user_state_path = user_root / ".agentbundle" / "state.toml"
    _write_state(user_state_path, _entry("user-pack", scope="user"))

    args = _make_args(root=str(repo_root), scope="local")

    with patch(
        "agentbundle.scope.resolve_user_root",
        return_value=user_root,
    ):
        rc = li.run(args)

    captured = capsys.readouterr()
    assert rc == 0
    assert "local-pack" in captured.out
    # local scope should not have loaded user-pack
    assert "user-pack" not in captured.out


# ---------------------------------------------------------------------------
# Test: --scope local annotation
# ---------------------------------------------------------------------------


def test_list_installed_scope_local_shows_annotation(tmp_path, capsys):
    """--scope local output includes the (not committed; per-clone only) note."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    local_state_path = repo_root / ".agentbundle-local-state.toml"
    _write_state(local_state_path, _entry("trial-pack", scope="local"))

    args = _make_args(root=str(repo_root), scope="local")

    rc = li.run(args)

    captured = capsys.readouterr()
    assert rc == 0
    assert "not committed" in captured.out or "per-clone" in captured.out
