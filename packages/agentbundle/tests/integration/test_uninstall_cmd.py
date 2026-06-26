"""T11: integration tests for ``agentbundle uninstall``.

Coverage:
  - Happy path: Tier-1 files removed; state no longer has the pack table.
  - Tier-2 preservation: adopter-edited file is byte-identical before and after.
  - Tier-3 byte-identity: adopter file outside the pack projection is untouched.
  - Multi-pack: uninstall A leaves [pack.B] in state and B's files untouched.
  - Missing pack: uninstall a name not in state exits non-zero with stderr.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

# Fixture catalogue reused from the install tests.
FIXTURE_CATALOGUE = (
    Path(__file__).parent.parent / "fixtures" / "install" / "catalogue"
)
ALPHA_PACK_DIR = FIXTURE_CATALOGUE / "packs" / "alpha"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_install(pack: str, catalogue: str, output: str) -> int:
    from agentbundle.commands.install import run
    # Test fixtures predate RFC-0012's per-IDE projection at repo scope;
    # pass `emit_install_routes=True` to keep the dist-tree shape these
    # tests assert against. The per-IDE projection path is covered by
    # the new `test_install_repo_scope_per_adapter.py` integration suite.
    return run(types.SimpleNamespace(
        pack=pack, catalogue=catalogue, output=output,
        emit_install_routes=True,
    ))


def _run_uninstall(
    pack: str, root: str, *, yes: bool = True, dry_run: bool = False
) -> int:
    from agentbundle.commands.uninstall import run
    # `yes=True` by default so the pre-existing non-prompt tests don't block on
    # input(); the confirmation-flow tests pass yes=False and monkeypatch
    # input/isatty (mirrors test_upgrade_cmd.py's `_run_upgrade`).
    return run(types.SimpleNamespace(
        pack=pack, root=root, yes=yes, dry_run=dry_run,
    ))


def _seed_state(tmp_path: Path, pack_name: str, files: dict[str, str]) -> None:
    """Write a minimal state file with known SHAs for testing."""
    from agentbundle.config import PackState, State, dump_state

    state = State()
    state.packs[(pack_name, "claude-code")] = PackState(
        installed_version="0.1.0",
        files={relpath: {"sha": sha, "from-pack-version": "0.1.0"} for relpath, sha in files.items()},
    )
    (tmp_path / ".agentbundle-state.toml").write_text(dump_state(state), encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Happy path: Tier-1 files are removed; state drops the pack table
# ---------------------------------------------------------------------------


def test_happy_path_tier1_files_removed(tmp_path):
    """Install alpha, then uninstall: every projected file must be gone and
    the [pack.alpha] table must no longer appear in the state file."""
    from agentbundle.config import load_state
    from agentbundle.render import render_pack

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0, "install must succeed"

    projection = render_pack(ALPHA_PACK_DIR)
    # Verify files exist before uninstall.
    for relpath in projection:
        assert (tmp_path / relpath).exists(), f"{relpath} should exist after install"

    rc = _run_uninstall("alpha", str(tmp_path))
    assert rc == 0, "uninstall must succeed"

    # Tier-1 files must be removed.
    for relpath in projection:
        assert not (tmp_path / relpath).exists(), f"{relpath} should be removed"

    # State must no longer reference the pack.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert not state.has_pack("alpha"), "[pack.alpha] must be absent after uninstall"


# ---------------------------------------------------------------------------
# 2. Tier-2 preservation: adopter-edited file is byte-identical before/after
# ---------------------------------------------------------------------------


def test_tier2_file_preserved_byte_identical(tmp_path):
    """After installing alpha, edit one file to produce a Tier-2 path.
    Uninstalling must leave that file byte-identical to its pre-uninstall state."""
    from agentbundle.render import render_pack

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    projection = render_pack(ALPHA_PACK_DIR)
    tier2_relpath = sorted(projection.keys())[0]
    tier2_file = tmp_path / tier2_relpath

    # Overwrite with adopter content (changes the SHA → Tier-2).
    adopter_content = b"adopter-edited content -- do not remove\n"
    tier2_file.write_bytes(adopter_content)

    before_bytes = tier2_file.read_bytes()

    rc = _run_uninstall("alpha", str(tmp_path))
    assert rc == 0, "uninstall must succeed even with a Tier-2 file"

    # Explicit byte-identity: must not have been removed or altered.
    assert tier2_file.exists(), "Tier-2 file must still exist"
    assert tier2_file.read_bytes() == before_bytes, (
        "Tier-2 file must be byte-identical before and after uninstall"
    )


# ---------------------------------------------------------------------------
# 3. Tier-3 byte-identity: adopter file outside the pack projection untouched
# ---------------------------------------------------------------------------


def test_tier3_file_byte_identical_before_and_after(tmp_path):
    """A file that is not part of the pack projection (Tier-3) must be
    byte-identical before and after uninstall."""
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    tier3_file = tmp_path / "src" / "adopter_owned.py"
    tier3_file.parent.mkdir(parents=True, exist_ok=True)
    tier3_content = b"# adopter source code\nprint('hello')\n"
    tier3_file.write_bytes(tier3_content)

    before_bytes = tier3_file.read_bytes()

    rc = _run_uninstall("alpha", str(tmp_path))
    assert rc == 0

    # Explicit byte-identity check.
    assert tier3_file.exists(), "Tier-3 file must still exist"
    assert tier3_file.read_bytes() == before_bytes, (
        "Tier-3 file must be byte-identical before and after uninstall"
    )


# ---------------------------------------------------------------------------
# 4. Multi-pack: uninstall A leaves [pack.B] and B's files untouched
# ---------------------------------------------------------------------------


def test_multi_pack_uninstall_a_preserves_b(tmp_path):
    """Install alpha and seed a second pack 'beta' in state. Uninstalling
    alpha must not touch [pack.beta] or any of beta's files."""
    from agentbundle.config import PackState, State, dump_state, load_state
    from agentbundle import safety

    # Install alpha normally.
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    # Add a second pack 'beta' to state manually, with one file on disk.
    beta_file = tmp_path / "docs" / "beta_readme.md"
    beta_file.parent.mkdir(parents=True, exist_ok=True)
    beta_content = b"# Beta pack documentation\n"
    beta_file.write_bytes(beta_content)
    beta_sha = safety.sha256_file(beta_file)

    # Reload state (alpha is there) and add beta.
    state_path = tmp_path / ".agentbundle-state.toml"
    state = load_state(state_path)
    state.packs[("beta", "claude-code")] = PackState(
        installed_version="1.0.0",
        files={"docs/beta_readme.md": {"sha": beta_sha, "from-pack-version": "1.0.0"}},
    )
    state_path.write_text(dump_state(state), encoding="utf-8")

    # Uninstall alpha.
    rc = _run_uninstall("alpha", str(tmp_path))
    assert rc == 0

    # [pack.beta] must still be present.
    updated_state = load_state(state_path)
    assert updated_state.has_pack("beta"), "[pack.beta] must survive uninstalling alpha"
    assert updated_state.row("beta", "claude-code").installed_version == "1.0.0"
    assert "docs/beta_readme.md" in updated_state.row("beta", "claude-code").files

    # beta's on-disk file must be byte-identical.
    assert beta_file.read_bytes() == beta_content, (
        "beta's file must be byte-identical after uninstalling alpha"
    )


# ---------------------------------------------------------------------------
# 5. Missing pack: uninstall a name not in state exits non-zero
# ---------------------------------------------------------------------------


def test_missing_pack_exits_nonzero(tmp_path, capsys):
    """Uninstalling a pack that is not in state must exit non-zero and print
    an appropriate message to stderr."""
    # Write an empty (but valid) state file.
    from agentbundle.config import State, dump_state

    state_path = tmp_path / ".agentbundle-state.toml"
    state_path.write_text(dump_state(State()), encoding="utf-8")

    rc = _run_uninstall("nonexistent", str(tmp_path))
    assert rc != 0, "uninstall of missing pack must exit non-zero"

    captured = capsys.readouterr()
    assert "nonexistent" in captured.err, (
        "stderr must mention the missing pack name"
    )


# ---------------------------------------------------------------------------
# 6. --dry-run / --yes / confirmation (CLI-hygiene AC1–AC5)
# ---------------------------------------------------------------------------


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    """Map every file under `root` to its bytes (for write-nothing assertions)."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_dry_run_previews_and_writes_nothing(tmp_path, capsys):
    """AC1: `uninstall --dry-run` prints the per-file plan + summary, exits 0,
    and mutates nothing — no file removed, no state change."""
    from agentbundle.render import render_pack

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    capsys.readouterr()  # drain install output

    before = _snapshot_tree(tmp_path)
    rc = _run_uninstall("alpha", str(tmp_path), dry_run=True)
    assert rc == 0, "dry-run must exit 0"

    out = capsys.readouterr().out
    assert "Nothing written." in out
    # Every projected file is previewed as `remove tier-1`.
    for relpath in render_pack(ALPHA_PACK_DIR):
        assert f"remove" in out and relpath in out

    assert _snapshot_tree(tmp_path) == before, "dry-run must write nothing"


def test_yes_skips_prompt(tmp_path, monkeypatch):
    """AC3: --yes proceeds without reading stdin."""
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    def _boom(prompt=""):
        raise AssertionError("input() must not be called with --yes")

    monkeypatch.setattr("builtins.input", _boom)
    rc = _run_uninstall("alpha", str(tmp_path), yes=True)
    assert rc == 0


def test_confirmation_accept_proceeds(tmp_path, monkeypatch):
    """AC2: an interactive 'y' proceeds with the removal."""
    from agentbundle.config import load_state

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "  YES ")
    rc = _run_uninstall("alpha", str(tmp_path), yes=False)
    assert rc == 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert not state.has_pack("alpha")


def test_confirmation_decline_writes_nothing(tmp_path, capsys, monkeypatch):
    """AC2: declining aborts and removes nothing."""
    from agentbundle.config import load_state

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    capsys.readouterr()
    before = _snapshot_tree(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    rc = _run_uninstall("alpha", str(tmp_path), yes=False)
    assert rc == 1
    assert "aborted" in capsys.readouterr().err
    assert _snapshot_tree(tmp_path) == before, "decline must write nothing"
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.has_pack("alpha"), "declined uninstall keeps the pack in state"


def test_confirmation_eof_treated_as_decline(tmp_path, capsys, monkeypatch):
    """AC2: EOF on the prompt declines."""
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    capsys.readouterr()

    def _raise(prompt=""):
        raise EOFError

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _raise)
    rc = _run_uninstall("alpha", str(tmp_path), yes=False)
    assert rc == 1
    assert "aborted" in capsys.readouterr().err


def test_non_tty_without_yes_refuses(tmp_path, capsys, monkeypatch):
    """AC4: a non-TTY stdin without --yes refuses, names --yes, writes nothing."""
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    capsys.readouterr()
    before = _snapshot_tree(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    def _boom(prompt=""):
        raise AssertionError("input() must not be called on a non-TTY")

    monkeypatch.setattr("builtins.input", _boom)
    rc = _run_uninstall("alpha", str(tmp_path), yes=False)
    assert rc == 1
    assert "--yes" in capsys.readouterr().err
    assert _snapshot_tree(tmp_path) == before, "refusal must write nothing"


def test_dry_run_remove_keep_parity_with_real_run(tmp_path, capsys):
    """AC5: the remove/keep split shown by --dry-run is exactly what a real
    --yes run removes/keeps (Tier-2 file shown `keep` is preserved byte-identical)."""
    from agentbundle.render import render_pack

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0
    capsys.readouterr()

    # Edit one projected file → Tier-2 (should be labelled `keep`).
    tier2_relpath = sorted(render_pack(ALPHA_PACK_DIR).keys())[0]
    tier2_file = tmp_path / tier2_relpath
    edited = b"adopter-edited -- keep me\n"
    tier2_file.write_bytes(edited)

    rc = _run_uninstall("alpha", str(tmp_path), dry_run=True)
    assert rc == 0
    plan = capsys.readouterr().out
    # Parse the plan lines into (decision, relpath).
    previewed_remove = set()
    previewed_keep = set()
    for line in plan.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in ("remove", "keep"):
            (previewed_remove if parts[0] == "remove" else previewed_keep).add(parts[2])
    assert tier2_relpath in previewed_keep
    assert tier2_relpath not in previewed_remove

    # Real run removes exactly the previewed `remove` set; keeps the Tier-2 file.
    rc = _run_uninstall("alpha", str(tmp_path), yes=True)
    assert rc == 0
    for relpath in previewed_remove:
        assert not (tmp_path / relpath).exists(), f"{relpath} previewed remove must be gone"
    assert tier2_file.read_bytes() == edited, "previewed `keep` file must be byte-identical"
