"""T12: show.py — _load_states includes local scope state.

Verifies that agentbundle show finds a pack installed only at local scope
and reports it as installed (source: installed-state).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from agentbundle.commands.show import _load_states
from agentbundle.config import PackState, State, dump_state


def _write_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8", newline="\n")


def test_load_states_includes_local_scope(tmp_path):
    """_load_states returns local state alongside repo and user."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Write only a local-scope state file
    local_ps = PackState(installed_version="0.2.0", scope="local")
    local_state = State(packs={("trial-pack", "claude-code"): local_ps})
    local_path = repo_root / ".agentbundle-local-state.toml"
    _write_state(local_path, local_state)

    args = argparse.Namespace(root=str(repo_root))

    from unittest.mock import patch

    from agentbundle.scope import UserScopeUnresolvable

    with patch("agentbundle.scope.resolve_user_root", side_effect=UserScopeUnresolvable("no home")):
        states = _load_states(args)

    # At least one state contains the local-scope pack
    found = any(("trial-pack", "claude-code") in s.packs for s in states)
    assert found, "local-scope pack not found in _load_states() result"


def test_load_states_local_pack_source_installed_state(tmp_path):
    """Pack installed only at local scope → source: installed-state."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Write only a local-scope state file
    local_ps = PackState(installed_version="0.2.0", scope="local", source="installed-state")
    local_state = State(packs={("trial-pack", "claude-code"): local_ps})
    _write_state(repo_root / ".agentbundle-local-state.toml", local_state)

    args = argparse.Namespace(root=str(repo_root))

    from unittest.mock import patch

    from agentbundle.scope import UserScopeUnresolvable

    with patch("agentbundle.scope.resolve_user_root", side_effect=UserScopeUnresolvable("no home")):
        states = _load_states(args)

    matching = [
        ps for s in states
        for (pack, adapter), ps in s.packs.items()
        if pack == "trial-pack"
    ]
    assert matching, "trial-pack not found in states"
    assert matching[0].source == "installed-state"
