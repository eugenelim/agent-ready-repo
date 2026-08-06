"""T10: uninstall.py — block-strip and worktree-id matching for local scope.

Tests:
- uninstall --scope local removes installed files
- uninstall strips only the correct worktree's block (sibling blocks untouched)
- Uninstalling one of two adapter rows recomputes block from remaining row's
  patterns; remaining row's files stay excluded
- Uninstalling the last adapter row strips the block entirely
- Uninstall removes only the specified adapter row from state; sibling rows remain
  File deleted when empty
- Disambiguator explicitly handles "local" scope (no else-fallthrough to repo)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"], check=True
    )


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    return repo


_FILE_CONTENT = b"content"  # canonical test file content


def _write_local_state(repo: Path, pack_name: str, adapter: str, relpaths: list[str]) -> None:
    """Write a minimal local state file with one pack row."""
    from agentbundle import safety
    from agentbundle.config import PackState, State, dump_state

    ps = PackState(
        installed_version="0.1.0",
        scope="local",
        adapter=adapter,
        files={r: {"sha": safety.sha256_bytes(_FILE_CONTENT), "from-pack-version": "0.1.0"} for r in relpaths},
    )
    st = State(packs={(pack_name, adapter): ps})
    state_path = repo / ".agentbundle-local-state.toml"
    state_path.write_text(dump_state(st), encoding="utf-8", newline="\n")


def _write_files(repo: Path, relpaths: list[str]) -> None:
    """Write placeholder files at the given repo-relative paths with canonical content."""
    for r in relpaths:
        target = repo / r
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_FILE_CONTENT)


def _write_exclude_block_for(repo: Path, pack: str, relpaths: list[str]) -> None:
    from agentbundle.local_exclude import (
        derive_worktree_id,
        get_exclude_path,
        write_exclude_block,
    )

    wid = derive_worktree_id(repo)
    ep = get_exclude_path(repo)
    ep.parent.mkdir(parents=True, exist_ok=True)
    patterns = ["/.agentbundle-local-state.toml"] + ["/" + r for r in sorted(relpaths)]
    write_exclude_block(ep, pack, wid, patterns)


# ---------------------------------------------------------------------------
# Scope disambiguator: local scope is recognised, not routed to repo
# ---------------------------------------------------------------------------


def test_disambiguator_infers_local_when_only_local(git_repo: Path) -> None:
    """If only local scope has the pack, effective_scope is 'local'."""
    relpaths = [".claude/skills/trial-pack/SKILL.md"]
    _write_local_state(git_repo, "trial-pack", "claude-code", relpaths)
    _write_files(git_repo, relpaths)
    _write_exclude_block_for(git_repo, "trial-pack", relpaths)

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope=None,
        adapter=None,
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0


def test_disambiguator_requires_scope_when_local_and_user(git_repo: Path) -> None:
    """If local + user scopes both have the pack, --scope is required."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from agentbundle import scope as scope_mod
    from agentbundle.config import PackState, State, dump_state

    relpaths = [".claude/skills/trial-pack/SKILL.md"]
    _write_local_state(git_repo, "trial-pack", "claude-code", relpaths)

    # Write user state with the same pack
    user_root = git_repo / "fake-home"
    user_root.mkdir()
    user_state_path = user_root / ".agentbundle" / "state.toml"
    user_state_path.parent.mkdir(parents=True, exist_ok=True)
    from agentbundle import safety
    ps = PackState(
        installed_version="0.1.0", scope="user",
        files={".claude/skills/trial-pack/SKILL.md": {"sha": safety.sha256_bytes(b"x"), "from-pack-version": "0.1.0"}}
    )
    st = State(packs={("trial-pack", "claude-code"): ps})
    user_state_path.write_text(dump_state(st), encoding="utf-8", newline="\n")

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope=None,  # no --scope → should require one
        adapter=None,
        dry_run=False,
        yes=True,
    )

    with patch.object(scope_mod, "resolve_user_root", return_value=user_root):
        from agentbundle.commands.uninstall import run
        rc = run(args)

    assert rc != 0  # should refuse; multiple scopes


# ---------------------------------------------------------------------------
# File removal
# ---------------------------------------------------------------------------


def test_uninstall_local_removes_files(git_repo: Path) -> None:
    """uninstall --scope local removes the installed files from the working tree."""
    relpaths = [".claude/skills/trial-pack/SKILL.md"]
    _write_local_state(git_repo, "trial-pack", "claude-code", relpaths)
    _write_files(git_repo, relpaths)
    _write_exclude_block_for(git_repo, "trial-pack", relpaths)

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope="local",
        adapter=None,
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0
    assert not (git_repo / ".claude" / "skills" / "trial-pack" / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# Exclude block: last adapter row → strip
# ---------------------------------------------------------------------------


def test_uninstall_last_adapter_strips_block(git_repo: Path) -> None:
    """Uninstalling the last adapter row strips the pack's exclude block."""
    from agentbundle.local_exclude import get_exclude_path

    relpaths = [".claude/skills/trial-pack/SKILL.md"]
    _write_local_state(git_repo, "trial-pack", "claude-code", relpaths)
    _write_files(git_repo, relpaths)
    _write_exclude_block_for(git_repo, "trial-pack", relpaths)

    exclude_path = get_exclude_path(git_repo)
    assert exclude_path.exists()
    before = exclude_path.read_text()
    assert "trial-pack" in before

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope="local",
        adapter=None,
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0

    after = exclude_path.read_text() if exclude_path.exists() else ""
    assert "trial-pack" not in after


# ---------------------------------------------------------------------------
# Exclude block: remaining adapter row → recompute
# ---------------------------------------------------------------------------


def test_uninstall_remaining_adapter_recomputes_block(git_repo: Path) -> None:
    """Uninstalling one of two adapters rewrites the block with the remaining patterns."""
    from agentbundle import safety
    from agentbundle.config import PackState, State, dump_state
    from agentbundle.local_exclude import get_exclude_path

    # Two adapter rows for the same pack
    relpaths_a = [".claude/skills/trial-pack/SKILL.md"]
    relpaths_b = [".kiro/skills/trial-pack/SKILL.md"]

    def _ps(scope_val, relpaths):
        return PackState(
            installed_version="0.1.0", scope=scope_val,
            files={r: {"sha": safety.sha256_bytes(_FILE_CONTENT), "from-pack-version": "0.1.0"} for r in relpaths},
        )

    st = State(packs={
        ("trial-pack", "claude-code"): _ps("local", relpaths_a),
        ("trial-pack", "kiro-cli"): _ps("local", relpaths_b),
    })
    state_path = git_repo / ".agentbundle-local-state.toml"
    state_path.write_text(dump_state(st), encoding="utf-8", newline="\n")
    _write_files(git_repo, relpaths_a + relpaths_b)

    # Write initial exclude block with union of both
    all_relpaths = relpaths_a + relpaths_b
    _write_exclude_block_for(git_repo, "trial-pack", all_relpaths)

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope="local",
        adapter="claude-code",
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0

    # claude-code file removed; kiro-cli file still present
    assert not (git_repo / relpaths_a[0]).exists()
    assert (git_repo / relpaths_b[0]).exists()

    # Block still exists (kiro-cli row remains) but no longer contains relpaths_a
    exclude_path = get_exclude_path(git_repo)
    block_content = exclude_path.read_text()
    assert "trial-pack" in block_content  # block still there
    assert relpaths_a[0] not in block_content  # claude-code path gone
    assert relpaths_b[0] in block_content  # kiro-cli path still there


# ---------------------------------------------------------------------------
# State file: deleted when empty
# ---------------------------------------------------------------------------


def test_uninstall_local_deletes_empty_state_file(git_repo: Path) -> None:
    """After uninstalling the last pack, .agentbundle-local-state.toml is deleted."""
    relpaths = [".claude/skills/trial-pack/SKILL.md"]
    _write_local_state(git_repo, "trial-pack", "claude-code", relpaths)
    _write_files(git_repo, relpaths)
    _write_exclude_block_for(git_repo, "trial-pack", relpaths)

    state_file = git_repo / ".agentbundle-local-state.toml"
    assert state_file.exists()

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope="local",
        adapter=None,
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0
    assert not state_file.exists(), "state file should be deleted when empty"


def test_uninstall_local_keeps_state_with_sibling_rows(git_repo: Path) -> None:
    """Uninstalling one adapter row leaves the state file with the sibling row."""
    from agentbundle import safety
    from agentbundle.config import PackState, State, dump_state, load_state

    def _ps(relpaths):
        return PackState(
            installed_version="0.1.0", scope="local",
            files={r: {"sha": safety.sha256_bytes(_FILE_CONTENT), "from-pack-version": "0.1.0"} for r in relpaths},
        )

    relpaths_a = [".claude/skills/trial-pack/SKILL.md"]
    relpaths_b = [".kiro/skills/trial-pack/SKILL.md"]
    st = State(packs={
        ("trial-pack", "claude-code"): _ps(relpaths_a),
        ("trial-pack", "kiro-cli"): _ps(relpaths_b),
    })
    state_path = git_repo / ".agentbundle-local-state.toml"
    state_path.write_text(dump_state(st), encoding="utf-8", newline="\n")
    _write_files(git_repo, relpaths_a + relpaths_b)
    _write_exclude_block_for(git_repo, "trial-pack", relpaths_a + relpaths_b)

    from types import SimpleNamespace

    from agentbundle.commands.uninstall import run

    args = SimpleNamespace(
        pack="trial-pack",
        root=str(git_repo),
        scope="local",
        adapter="claude-code",
        dry_run=False,
        yes=True,
    )
    rc = run(args)
    assert rc == 0

    # State file should still exist (kiro-cli row remains)
    assert state_path.exists()
    remaining = load_state(state_path)
    assert ("trial-pack", "kiro-cli") in remaining.packs
    assert ("trial-pack", "claude-code") not in remaining.packs
