"""T10: Tests for `init-state` subcommand.

Three scenarios:
  1. Happy path — render core into tmpdir, run init-state, assert state file is
     parseable by config.load_state and every file's SHA matches.
  2. Merge — pre-populate .agent-ready-state.toml with [pack.A]; run
     init-state --pack core; assert [pack.A] still present.
  3. Tier invariant — only .agent-ready-state.toml is written; no other paths
     changed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

from agentbundle import config, render
from agentbundle.commands import init_state

# Resolve the repo root and core pack path relative to this file's location.
# Layout: packages/agentbundle/tests/unit/test_init_state_cmd.py
# Repo root is four parents up.
REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"
CORE_PACK = PACKS_DIR / "core"


def _make_args(
    *,
    pack: str = "core",
    packs_dir: str | None = None,
    root: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        pack=pack,
        packs_dir=str(packs_dir) if packs_dir is not None else str(PACKS_DIR),
        root=root,
    )


def _project_pack_into(pack_path: Path, root: Path) -> dict[str, bytes]:
    """Render a pack in-memory and write every projected file to *root*."""
    rendered = render.render_pack(pack_path)
    for relpath, content in rendered.items():
        dest = root / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return rendered


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_init_state_happy_path(tmp_path):
    """After projecting the core pack and running init-state, the state file
    must be parseable and every file's SHA must match its on-disk content."""
    rendered = _project_pack_into(CORE_PACK, tmp_path)

    args = _make_args(root=str(tmp_path))
    rc = init_state.run(args)
    assert rc == 0, "init-state should exit 0 on success"

    state_path = tmp_path / ".agent-ready-state.toml"
    assert state_path.exists(), ".agent-ready-state.toml must be written"

    state = config.load_state(state_path)
    assert "core" in state.packs, "[pack.core] must be present"

    pack_state = state.packs["core"]
    for relpath, content in rendered.items():
        expected_sha = hashlib.sha256(content).hexdigest()
        actual_sha = pack_state.file_sha(relpath)
        assert actual_sha is not None, f"no SHA recorded for {relpath}"
        assert actual_sha == expected_sha, (
            f"SHA mismatch for {relpath}: expected {expected_sha}, got {actual_sha}"
        )


# ---------------------------------------------------------------------------
# Merge: existing pack table untouched
# ---------------------------------------------------------------------------


def test_init_state_merge_preserves_other_pack(tmp_path):
    """Pre-populate [pack.A]; run init-state --pack core; assert [pack.A] survives."""
    # Write a minimal state file with a different pack.
    pre_state = config.State()
    pre_state.packs["A"] = config.PackState(
        installed_version="1.0.0",
        files={"some/path.md": {"sha": "deadbeef", "from-pack-version": "1.0.0"}},
    )
    (tmp_path / ".agent-ready-state.toml").write_text(
        config.dump_state(pre_state), encoding="utf-8"
    )

    _project_pack_into(CORE_PACK, tmp_path)

    args = _make_args(root=str(tmp_path))
    rc = init_state.run(args)
    assert rc == 0

    state = config.load_state(tmp_path / ".agent-ready-state.toml")
    assert "A" in state.packs, "[pack.A] must survive the merge"
    assert state.packs["A"].file_sha("some/path.md") == "deadbeef"
    assert "core" in state.packs, "[pack.core] must be added"


# ---------------------------------------------------------------------------
# Tier invariant: only .agent-ready-state.toml is written
# ---------------------------------------------------------------------------


def test_init_state_writes_only_state_file(tmp_path):
    """init-state must not write any file other than .agent-ready-state.toml."""
    _project_pack_into(CORE_PACK, tmp_path)

    # Snapshot the tree before init-state.
    def _snapshot(root: Path) -> dict[str, bytes]:
        return {
            p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    before = _snapshot(tmp_path)

    args = _make_args(root=str(tmp_path))
    rc = init_state.run(args)
    assert rc == 0

    after = _snapshot(tmp_path)
    state_relpath = ".agent-ready-state.toml"

    # Exactly one new file: the state file.
    new_files = set(after) - set(before)
    assert new_files == {state_relpath}, (
        f"init-state must create only {state_relpath}; created {new_files}"
    )

    # No existing projected file was mutated.
    for relpath in before:
        assert before[relpath] == after[relpath], (
            f"init-state must not modify existing file: {relpath}"
        )


# ---------------------------------------------------------------------------
# Error path: missing pack directory
# ---------------------------------------------------------------------------


def test_init_state_missing_pack_exits_nonzero(tmp_path):
    """init-state with --pack nonexistent should return a non-zero exit code."""
    args = _make_args(pack="nonexistent", root=str(tmp_path))
    rc = init_state.run(args)
    assert rc != 0, "expected non-zero exit for missing pack"
