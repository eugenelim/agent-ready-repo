# STUB: AC-0003, AC-0026, AC-0002, AC-0024, AC-0013
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pytest

_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-rename-test.md"
TOMBSTONE_DATE = date(2026, 9, 29)


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


_SANDBOX_STAGE_REMOVALS: list[str] = []


def _sandbox_remove_empty_stage(parent_descriptor: int, name: str) -> None:
    """Replace only the sandbox-blocked final rmdir with an empty-dir rename."""
    descriptor = os.open(
        name,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_descriptor,
    )
    try:
        assert os.listdir(descriptor) == []  # noqa: PTH208 - held no-follow fd
    finally:
        os.close(descriptor)
    # Renaming out of the stage namespace keeps the result observable as the
    # runtime sees it: no recovery candidate remains.
    os.rename(
        name,
        ".sandbox-disposed-" + name,
        src_dir_fd=parent_descriptor,
        dst_dir_fd=parent_descriptor,
    )
    _SANDBOX_STAGE_REMOVALS.append(name)


rename._remove_empty_stage = _sandbox_remove_empty_stage


# The child loads the operator and drives its real CLI `main` with an
# in-process checkpoint that SIGKILLs the process. The installed entry point
# exposes no such seam, so a real kill needs this test-owned driver.
_KILL_CHILD = """
import datetime
import importlib.util
import os
import signal
import sys
from pathlib import Path

script, checkpoint, today = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
sandbox_cleanup = sys.argv[4] == "1"
spec = importlib.util.spec_from_file_location(
    "core_work_intake_intent_rename_kill_child", script
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def remove_empty_stage(parent_descriptor, name):
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    try:
        if os.listdir(descriptor):
            raise RuntimeError("stage-not-empty")
    finally:
        os.close(descriptor)
    os.rename(
        name,
        ".sandbox-disposed-" + name,
        src_dir_fd=parent_descriptor,
        dst_dir_fd=parent_descriptor,
    )

def kill_at(name):
    if name == checkpoint:
        os.kill(os.getpid(), signal.SIGKILL)

if sandbox_cleanup:
    module._remove_empty_stage = remove_empty_stage
raise SystemExit(
    module.main(
        sys.argv[5:],
        _checkpoint=kill_at,
        _today=lambda: datetime.date.fromisoformat(today),
    )
)
"""


def _commit(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _fixture(root: Path, *, needs_edge: bool = False) -> bytes:
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source_bytes = (
        "# Rename test\n\n"
        "- **Slug:** `rename-test`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n\n"
        f"Self: {SOURCE}\n"
    ).encode()
    source.write_bytes(source_bytes)
    (root / "citation.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    entry = (
        f'{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}'
    )
    entries = [entry]
    if needs_edge:
        other = "docs/product/intents/FEAT-0002-unaffected.md"
        other_path = root / other
        other_path.write_text(
            "# Other\n\n- **Slug:** `unaffected`\n- **Status:** Draft\n",
            encoding="utf-8",
        )
        entries.append(
            f'{{path = "{other}", kind = "intent", '
            'source = {mode = "repo-origin"}, summary = "other", '
            f'needs = [{{type = "local", kind = "intent", path = "{SOURCE}"}}]}}'
        )
    (root / "workspace.toml").write_text(
        f"[backlog]\nopen = [{', '.join(entries)}]\n",
        encoding="utf-8",
    )
    _commit(root)
    return source_bytes


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def _stage_payloads(root: Path) -> list[Path]:
    return [
        child
        for stage in (root / "docs/product/intents").glob(".intent-rename-*")
        if stage.name not in _SANDBOX_STAGE_REMOVALS
        for child in stage.iterdir()
    ]


def _stage_dirs(root: Path) -> list[Path]:
    return [
        stage
        for stage in (root / "docs/product/intents").glob(".intent-rename-*")
        if stage.name not in _SANDBOX_STAGE_REMOVALS
    ]


def _interrupt_after_successor(checkpoint: str) -> None:
    if checkpoint == "after-successor":
        raise rename.InjectedInterruption(checkpoint)


def _interrupt(name: str) -> Any:
    def checkpoint(checkpoint_name: str) -> None:
        if checkpoint_name == name:
            raise rename.InjectedInterruption(checkpoint_name)

    return checkpoint


def _kill_rename(root: Path, checkpoint: str) -> None:
    _kill_operator(root, ["rename", SOURCE, "STRAT"], checkpoint)


def _kill_operator(
    root: Path,
    arguments: list[str],
    checkpoint: str,
    *,
    sandbox_cleanup: bool = False,
) -> None:
    command = [
        sys.executable,
        "-c",
        _KILL_CHILD,
        os.fspath(SCRIPT),
        checkpoint,
        TOMBSTONE_DATE.isoformat(),
        "1" if sandbox_cleanup else "0",
        *arguments,
    ]
    result = subprocess.run(
        command,
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    assert result.returncode == -signal.SIGKILL, result


def _kill_recovery(root: Path, direction: str, checkpoint: str) -> None:
    _kill_operator(
        root,
        ["recover", direction, SOURCE, "STRAT", TOMBSTONE_DATE.isoformat()],
        checkpoint,
    )


def _assert_no_recovery_residue(root: Path) -> None:
    """A terminal state leaves no lock, temporary, or recovery candidate stage."""
    assert not (root / ".workspace-repair.lock").exists()
    assert not list(root.rglob(".intent-rename-*.tmp"))
    assert not [
        stage
        for stage in (root / "docs/product/intents").glob(".intent-rename-*")
        if not stage.name.endswith(".tmp")
    ]


_FORWARD_REFERENCE: dict[str, bytes] = {}


def _forward_reference_tree() -> dict[str, bytes]:
    """The complete all-after tree: an uninterrupted rename of the same fixture."""
    if not _FORWARD_REFERENCE:
        reference = Path(tempfile.mkdtemp(prefix="intent-rename-reference-"))
        try:
            _fixture(reference)
            result = rename.run_intent_rename(
                SOURCE, "STRAT", repository_root=reference, _today=lambda: TOMBSTONE_DATE
            )
            assert result.status is rename.RenameStatus.COMMITTED, result
            _FORWARD_REFERENCE.update(_tree(reference))
        finally:
            shutil.rmtree(reference, ignore_errors=True)
    return _FORWARD_REFERENCE


def _assert_forward_terminal(root: Path, source_before: bytes) -> None:
    # The whole tree, byte for byte, so a recovery that also touched an
    # unrelated file cannot pass on the named files alone.
    assert _tree(root) == _forward_reference_tree()
    expected_successor = source_before.replace(SOURCE.encode(), SUCCESSOR.encode())
    assert (root / SUCCESSOR).read_bytes() == expected_successor
    assert f"- **Reissued as:** {SUCCESSOR}" in (root / SOURCE).read_text(encoding="utf-8")
    assert (root / "citation.md").read_text(encoding="utf-8") == f"See {SUCCESSOR}.\n"
    workspace = (root / "workspace.toml").read_text(encoding="utf-8")
    assert SOURCE not in workspace
    assert SUCCESSOR in workspace
    _assert_no_recovery_residue(root)


def _assert_back_terminal(root: Path, before: dict[str, bytes]) -> None:
    assert _tree(root) == before
    for relative, data in before.items():
        assert (root / relative).read_bytes() == data
    assert not (root / SUCCESSOR).exists()
    _assert_no_recovery_residue(root)


def test_ac_0003_preapply_refusal_leaves_tree_and_index_unchanged(tmp_path: Path) -> None:
    _fixture(tmp_path)
    before = _tree(tmp_path)
    result = rename.run_intent_rename(SOURCE, "UNKNOWN", repository_root=tmp_path)

    assert result.code == "token-unknown"
    assert _tree(tmp_path) == before
    assert (
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, check=True, capture_output=True
        ).stdout
        == b""
    )


def test_ac_0026_both_recovery_directions_reach_only_an_end_state(tmp_path: Path) -> None:
    forward_root = tmp_path / "forward"
    back_root = tmp_path / "back"
    forward_root.mkdir()
    back_root.mkdir()
    _fixture(forward_root)
    before_back = _fixture(back_root)

    forward_partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=forward_root,
        _checkpoint=_interrupt_after_successor,
        _today=lambda: TOMBSTONE_DATE,
    )
    back_partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=back_root,
        _checkpoint=_interrupt_after_successor,
        _today=lambda: TOMBSTONE_DATE,
    )
    assert forward_partial.status is rename.RenameStatus.PARTIAL
    assert back_partial.status is rename.RenameStatus.PARTIAL

    forward = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=forward_root,
    )
    backward = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=back_root,
    )

    assert forward.status is rename.RenameStatus.COMMITTED
    assert (forward_root / SUCCESSOR).is_file()
    assert backward.status is rename.RenameStatus.ROLLED_BACK
    assert (back_root / SOURCE).read_bytes() == before_back
    assert not (back_root / SUCCESSOR).exists()
    assert not _stage_payloads(back_root)


def test_ac_0002_and_ac_0024_successor_and_slug_bytes_are_conserved(tmp_path: Path) -> None:
    source_bytes = _fixture(tmp_path)
    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    expected = source_bytes.replace(SOURCE.encode(), SUCCESSOR.encode())
    assert (tmp_path / SUCCESSOR).read_bytes() == expected
    assert b"- **Slug:** `rename-test`" in (tmp_path / SUCCESSOR).read_bytes()
    assert b"- **Slug:** `rename-test`" in (tmp_path / SOURCE).read_bytes()


def test_ac_0013_valid_request_commits_tombstone_and_registry(tmp_path: Path) -> None:
    _fixture(tmp_path)
    removals_before = len(_SANDBOX_STAGE_REMOVALS)
    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    tombstone = (tmp_path / SOURCE).read_text(encoding="utf-8")
    assert f"- **Reissued as:** {SUCCESSOR}" in tombstone
    workspace = (tmp_path / "workspace.toml").read_text(encoding="utf-8")
    assert SOURCE not in workspace
    assert SUCCESSOR in workspace
    assert len(_SANDBOX_STAGE_REMOVALS) == removals_before + 1


def test_t1_registry_membership_and_needs_repoint_without_touching_unaffected_intent(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path, needs_edge=True)
    unaffected = tmp_path / "docs/product/intents/FEAT-0002-unaffected.md"
    before_unaffected = unaffected.read_bytes()

    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    workspace = (tmp_path / "workspace.toml").read_text(encoding="utf-8")
    assert SOURCE not in workspace
    assert workspace.count(SUCCESSOR) == 2
    assert unaffected.read_bytes() == before_unaffected
    assert not _stage_payloads(tmp_path)
    assert not (tmp_path / ".workspace-repair.lock").exists()


def test_t1_real_kill_after_successor_hard_link_recovers_forward(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-successor")
    stage = _stage_dirs(tmp_path)[0]

    assert (tmp_path / SUCCESSOR).exists()
    assert (tmp_path / SUCCESSOR).stat().st_ino == (stage / "0000.postimage").stat().st_ino

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.COMMITTED
    assert (tmp_path / SUCCESSOR).is_file()
    assert f"- **Reissued as:** {SUCCESSOR}" in (tmp_path / SOURCE).read_text(encoding="utf-8")
    assert not _stage_payloads(tmp_path)


def test_t1_real_kill_after_lock_link_clears_owned_stranded_lock(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-lock-link")
    stage = _stage_dirs(tmp_path)[0]

    assert (tmp_path / ".workspace-repair.lock").exists()
    assert (tmp_path / ".workspace-repair.lock").stat().st_ino == (
        stage / "lock.claim"
    ).stat().st_ino

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.COMMITTED
    assert not (tmp_path / ".workspace-repair.lock").exists()
    assert not _stage_payloads(tmp_path)


@pytest.mark.parametrize(
    ("checkpoint_name", "error"),
    [
        ("after-lock-link", ValueError("ordinary-value-error")),
        ("before-registry", OSError("ordinary-os-error")),
        ("after-registry", ValueError("ordinary-value-error")),
    ],
)
def test_t1_registry_exception_releases_the_owned_shared_lock(
    tmp_path: Path, checkpoint_name: str, error: Exception
) -> None:
    _fixture(tmp_path)

    def fail(checkpoint: str) -> None:
        if checkpoint == checkpoint_name:
            raise error

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=fail,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "transaction-refused"
    assert result.operation_id is not None
    assert not (tmp_path / ".workspace-repair.lock").exists()
    assert not (_stage_dirs(tmp_path)[0] / "lock.claim").exists()


@pytest.mark.parametrize(
    "corruption",
    [b"[backlog\nnot toml", b"[backlog]\nopen = []\n"],
    ids=["unparseable", "source-unregistered"],
)
def test_t1_real_registry_errors_release_the_owned_shared_lock(
    tmp_path: Path, corruption: bytes
) -> None:
    """An error raised by the registry code itself, not an injected one, releases the lock."""
    _fixture(tmp_path)

    def corrupt_registry_once_locked(checkpoint: str) -> None:
        if checkpoint == "after-lock-link":
            (tmp_path / "workspace.toml").write_bytes(corruption)

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=corrupt_registry_once_locked,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.operation_id is not None
    assert not (tmp_path / ".workspace-repair.lock").exists()
    assert not (_stage_dirs(tmp_path)[0] / "lock.claim").exists()


def test_t1_registry_exception_never_unlinks_a_foreign_shared_lock(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    foreign_inode: int | None = None

    def replace_lock_then_fail(checkpoint: str) -> None:
        nonlocal foreign_inode
        if checkpoint != "before-registry":
            return
        lock = tmp_path / ".workspace-repair.lock"
        lock.unlink()
        lock.write_bytes(b"foreign")
        foreign_inode = lock.stat().st_ino
        raise OSError("ordinary-os-error")

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=replace_lock_then_fail,
        _today=lambda: TOMBSTONE_DATE,
    )

    stage_claim = _stage_dirs(tmp_path)[0] / "lock.claim"
    lock = tmp_path / ".workspace-repair.lock"
    assert result.status is rename.RenameStatus.PARTIAL
    assert result.code == "lock-release-failed"
    assert result.operation_id is not None
    assert foreign_inode is not None
    assert lock.stat().st_ino == foreign_inode
    assert stage_claim.exists()
    assert stage_claim.stat().st_ino != foreign_inode


def test_t1_registry_exception_preserves_an_owned_lock_with_an_extra_link(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    extra = tmp_path / "extra-lock-link"
    alien_inode: int | None = None

    def add_extra_link_then_fail(checkpoint: str) -> None:
        nonlocal alien_inode
        if checkpoint != "before-registry":
            return
        claim = _stage_dirs(tmp_path)[0] / "lock.claim"
        os.link(claim, extra)
        alien_inode = claim.stat().st_ino
        raise OSError("ordinary-os-error")

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=add_extra_link_then_fail,
        _today=lambda: TOMBSTONE_DATE,
    )

    claim = _stage_dirs(tmp_path)[0] / "lock.claim"
    lock = tmp_path / ".workspace-repair.lock"
    assert result.status is rename.RenameStatus.PARTIAL
    assert result.code == "lock-release-failed"
    assert result.operation_id is not None
    assert alien_inode is not None
    assert {
        claim.stat().st_ino,
        lock.stat().st_ino,
        extra.stat().st_ino,
    } == {alien_inode}
    assert claim.stat().st_nlink == lock.stat().st_nlink == extra.stat().st_nlink == 3
    assert claim.read_bytes() == lock.read_bytes() == extra.read_bytes()


def test_t1_registry_exception_preserves_an_owned_lock_with_alien_payload(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    alien_payload = b"not-a-pid"

    def replace_claim_payload_then_fail(checkpoint: str) -> None:
        if checkpoint != "before-registry":
            return
        (_stage_dirs(tmp_path)[0] / "lock.claim").write_bytes(alien_payload)
        raise OSError("ordinary-os-error")

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=replace_claim_payload_then_fail,
        _today=lambda: TOMBSTONE_DATE,
    )

    claim = _stage_dirs(tmp_path)[0] / "lock.claim"
    lock = tmp_path / ".workspace-repair.lock"
    assert result.status is rename.RenameStatus.PARTIAL
    assert result.code == "lock-release-failed"
    assert result.operation_id is not None
    assert claim.stat().st_ino == lock.stat().st_ino
    assert claim.stat().st_nlink == lock.stat().st_nlink == 2
    assert claim.read_bytes() == lock.read_bytes() == alien_payload


def test_ac_0026_rerun_beside_an_unattributed_stage_refuses_until_recovered(
    tmp_path: Path,
) -> None:
    """A stage killed before its record exists is never left behind by a rerun."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-stage-created")
    (stage,) = _stage_dirs(tmp_path)
    assert list(stage.iterdir()) == []

    rerun = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert rerun.status is rename.RenameStatus.REFUSED
    assert rerun.code == "recovery-required"
    assert _stage_dirs(tmp_path) == [stage]
    assert _tree(tmp_path) == before

    recovered = rename.recover_intent_rename(
        "back", SOURCE, "STRAT", TOMBSTONE_DATE.isoformat(), repository_root=tmp_path
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    assert _stage_dirs(tmp_path) == []
    assert _tree(tmp_path) == before


@pytest.mark.parametrize("direction", ["forward", "back"])
@pytest.mark.parametrize("cut", ["empty", "one", "half", "all-but-one"])
def test_ac_0026_partial_record_stage_can_only_end_pre_rename(
    tmp_path: Path, cut: str, direction: str
) -> None:
    """A record killed mid-write precedes every live write, so the terminal is pre-rename."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-record")
    (stage,) = _stage_dirs(tmp_path)
    _tear(stage / "record.json", cut)

    rerun = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )
    assert rerun.code == "recovery-required"
    assert _stage_dirs(tmp_path) == [stage]

    recovered = rename.recover_intent_rename(
        direction, SOURCE, "STRAT", TOMBSTONE_DATE.isoformat(), repository_root=tmp_path
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    assert _stage_dirs(tmp_path) == []
    assert _tree(tmp_path) == before


@pytest.mark.parametrize(
    ("limit", "value"),
    [
        ("_MAX_RECORD_BYTES", 64),
        ("_MAX_SEAL_BYTES", 64),
        ("_MAX_CITING_BYTES", 64),
        ("_MAX_JSON_STRING", 16),
        ("_MAX_REGISTRY_MERGE_LINES", 1),
        ("_MAX_RECOVERY_CANDIDATES", 0),
    ],
)
def test_t1_stage_budget_refuses_before_any_stage_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str, value: int
) -> None:
    """Every artifact recovery reads under a ceiling is admitted under it first."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    monkeypatch.setattr(rename, limit, value)

    result = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "stage-budget"
    assert _stage_dirs(tmp_path) == []
    assert _tree(tmp_path) == before


def test_t1_forward_registry_image_over_the_workspace_ceiling_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The longer successor path cannot grow `workspace.toml` past its ceiling."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    workspace = (tmp_path / "workspace.toml").read_bytes()
    successor = rename.derive_successor_path(SOURCE, "STRAT", repository_root=tmp_path)
    assert len(successor) > len(SOURCE)
    monkeypatch.setattr(rename, "_MAX_WORKSPACE_BYTES", len(workspace))

    with pytest.raises(ValueError, match="registry-bound"):
        rename._workspace_transition(workspace, SOURCE, successor, "forward")
    result = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert result.code == "stage-budget"
    assert _stage_dirs(tmp_path) == []
    assert _tree(tmp_path) == before


def _tear(path: Path, cut: str) -> None:
    """Leave the proper prefix a kill mid-write would: empty, one byte, half, all but one."""
    data = path.read_bytes()
    keep = {"empty": 0, "one": 1, "half": len(data) // 2, "all-but-one": len(data) - 1}[cut]
    path.write_bytes(data[:keep])


_CUTS = ["empty", "one", "half", "all-but-one"]


def _recover(root: Path, direction: str) -> Any:
    return rename.recover_intent_rename(
        direction, SOURCE, "STRAT", TOMBSTONE_DATE.isoformat(), repository_root=root
    )


@pytest.mark.parametrize("direction", ["forward", "back"])
@pytest.mark.parametrize("cut", _CUTS)
def test_ac_0026_torn_seal_on_an_untouched_tree_is_discarded(
    tmp_path: Path, direction: str, cut: str
) -> None:
    """A seal killed mid-write grants nothing, and the untouched stage is discarded."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-seal")
    (stage,) = _stage_dirs(tmp_path)
    _tear(stage / "complete.json", cut)

    result = _recover(tmp_path, direction)

    assert result.status is rename.RenameStatus.ROLLED_BACK
    assert _tree(tmp_path) == before
    _assert_no_recovery_residue(tmp_path)


@pytest.mark.parametrize(
    ("checkpoint", "name"),
    [("after-record", "record.json"), ("after-seal", "complete.json"), ("after-cleanup-marker", "cleanup.json")],
)
def test_ac_0026_altered_stage_metadata_is_refused_and_kept(
    tmp_path: Path, checkpoint: str, name: str
) -> None:
    """Bytes that are not a prefix of the canonical artifact were altered, not torn."""
    _fixture(tmp_path)
    _kill_rename(tmp_path, checkpoint)
    (stage,) = _stage_dirs(tmp_path)
    original = (stage / name).read_bytes()
    (stage / name).write_bytes(original[:-2] + b"X}")
    staged = _tree(tmp_path)

    for direction in ("forward", "back"):
        result = _recover(tmp_path, direction)

        assert result.status is rename.RenameStatus.REFUSED
        assert _tree(tmp_path) == staged


def test_ac_0026_invalid_seal_never_authorizes_a_live_mutation(tmp_path: Path) -> None:
    """Once live writes began, an invalid seal refuses rather than guessing a direction."""
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-successor")
    (stage,) = _stage_dirs(tmp_path)
    (stage / "complete.json").write_bytes(b'{"version":1}')
    partial = _tree(tmp_path)

    for direction in ("forward", "back"):
        result = _recover(tmp_path, direction)

        assert result.status is rename.RenameStatus.REFUSED
        assert _tree(tmp_path) == partial


@pytest.mark.parametrize("checkpoint", ["after-cleanup-marker", "after-dispose-record"])
def test_ac_0026_torn_cleanup_marker_finishes_from_the_proven_terminal(
    tmp_path: Path, checkpoint: str
) -> None:
    """A marker killed mid-write names no direction; the proven terminal state does."""
    source_before = _fixture(tmp_path)
    _kill_rename(tmp_path, checkpoint)
    (stage,) = _stage_dirs(tmp_path)
    _tear(stage / "cleanup.json", "half")

    result = _recover(tmp_path, "back")

    assert result.status is rename.RenameStatus.COMMITTED
    _assert_forward_terminal(tmp_path, source_before)
    _assert_no_recovery_residue(tmp_path)


def test_ac_0026_real_sigkill_while_restoring_a_torn_marker_recovers(
    tmp_path: Path,
) -> None:
    source_before = _fixture(tmp_path)
    _kill_rename(tmp_path, "after-cleanup-marker")
    (stage,) = _stage_dirs(tmp_path)
    _tear(stage / "cleanup.json", "half")

    _kill_recovery(tmp_path, "forward", "after-torn-cleanup-removed")
    result = _recover(tmp_path, "forward")

    assert result.status is rename.RenameStatus.COMMITTED
    _assert_forward_terminal(tmp_path, source_before)
    _assert_no_recovery_residue(tmp_path)


def test_ac_0026_real_sigkill_while_disposing_a_partial_record_recovers(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-record")
    (stage,) = _stage_dirs(tmp_path)
    _tear(stage / "record.json", "half")

    _kill_recovery(tmp_path, "back", "after-dispose-partial-record")
    result = _recover(tmp_path, "back")

    assert result.status is rename.RenameStatus.ROLLED_BACK
    assert _tree(tmp_path) == before
    _assert_no_recovery_residue(tmp_path)


def test_ac_0026_back_recovery_restores_repeated_registry_lines_exactly(
    tmp_path: Path,
) -> None:
    """Identical lines naming the source are restored byte for byte."""
    _fixture(tmp_path)
    workspace = tmp_path / "workspace.toml"
    comment = f"# tracked as {SOURCE}\n"
    workspace.write_bytes((comment * 2).encode() + workspace.read_bytes())
    subprocess.run(["git", "add", "workspace.toml"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "repeat"], cwd=tmp_path, check=True, capture_output=True
    )
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-registry")
    assert SOURCE not in workspace.read_text(encoding="utf-8")

    result = _recover(tmp_path, "back")

    assert result.status is rename.RenameStatus.ROLLED_BACK
    assert _tree(tmp_path) == before
    _assert_no_recovery_residue(tmp_path)


def _commit_modes(root: Path) -> None:
    """Give the citing file an executable bit Git tracks, and the source a non-default mode."""
    (root / "citation.md").chmod(0o755)
    (root / SOURCE).chmod(0o640)
    subprocess.run(["git", "add", "citation.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "modes"], cwd=root, check=True, capture_output=True)


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_ac_0026_rename_and_rollback_preserve_file_modes(tmp_path: Path) -> None:
    """Replaced files keep their mode, and the successor takes the source's."""
    forward = tmp_path / "forward"
    forward.mkdir()
    _fixture(forward)
    _commit_modes(forward)

    renamed = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=forward, _today=lambda: TOMBSTONE_DATE
    )

    assert renamed.status is rename.RenameStatus.COMMITTED, renamed
    assert _mode(forward / "citation.md") == 0o755
    assert _mode(forward / SOURCE) == 0o640
    assert _mode(forward / SUCCESSOR) == 0o640

    back = tmp_path / "back"
    back.mkdir()
    _fixture(back)
    _commit_modes(back)
    before = _tree(back)
    _kill_rename(back, "after-replace-2")

    rolled = _recover(back, "back")

    assert rolled.status is rename.RenameStatus.ROLLED_BACK
    assert _tree(back) == before
    assert _mode(back / "citation.md") == 0o755
    assert _mode(back / SOURCE) == 0o640


def test_t1_registry_line_bound_is_rechecked_under_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A concurrent edit after admission cannot carry the image past the merge bound."""
    _fixture(tmp_path)
    workspace = tmp_path / "workspace.toml"
    lines = len(workspace.read_bytes().splitlines())
    monkeypatch.setattr(rename, "_MAX_REGISTRY_MERGE_LINES", lines + 2)

    def grow_registry(checkpoint: str) -> None:
        if checkpoint == "after-lock-link":
            workspace.write_bytes(workspace.read_bytes() + b"# concurrent\n" * 5)

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=grow_registry,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert SOURCE in workspace.read_text(encoding="utf-8")
    assert SUCCESSOR not in workspace.read_text(encoding="utf-8")
    assert not (tmp_path / ".workspace-repair.lock").exists()


def test_t2_selected_stage_refusals_carry_its_operation_id(tmp_path: Path) -> None:
    """A fixed refusal about one stage names that stage."""
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-seal")
    (stage,) = _stage_dirs(tmp_path)
    (tmp_path / "citation.md").write_text("Altered after staging.\n", encoding="utf-8")

    result = _recover(tmp_path, "forward")

    assert result.status is rename.RenameStatus.REFUSED
    assert result.operation_id == stage.name.removeprefix(".intent-rename-")


def test_ac_0026_unusable_stage_is_reported_not_treated_as_absent(tmp_path: Path) -> None:
    """A present stage whose record names no request refuses with its id, not as missing."""
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-seal")
    (stage,) = _stage_dirs(tmp_path)
    record = stage / "record.json"
    record.write_bytes(record.read_bytes()[:-2] + b"X}")
    staged = _tree(tmp_path)

    result = _recover(tmp_path, "forward")

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "stage-unattributed"
    assert result.operation_id == stage.name.removeprefix(".intent-rename-")
    assert _tree(tmp_path) == staged


_RECOVERY_START = {"forward": "after-seal", "back": "after-registry"}
_DISPOSAL_CHECKPOINTS = (
    "after-terminal-validation",
    "after-cleanup-marker",
    "after-dispose-postimage-0",
    "after-dispose-postimage-1",
    "after-dispose-postimage-2",
    "after-dispose-seal",
    "after-dispose-record",
    "after-dispose-cleanup",
    "after-stage-cleanup",
)
# Pinned, so removing a checkpoint around a write fails here rather than
# silently shrinking the kill matrix below.
_RECOVERY_CHECKPOINTS = {
    "forward": (
        "after-successor",
        "after-temporary-1",
        "after-replace-1",
        "after-temporary-2",
        "after-replace-2",
        "after-lock-claim",
        "after-lock-link",
        "before-registry",
        "after-temporary-3",
        "after-replace-3",
        "after-registry",
        "after-lock-release",
        *_DISPOSAL_CHECKPOINTS,
    ),
    "back": (
        "after-successor-remove",
        "after-lock-claim",
        "after-lock-link",
        "before-registry",
        "after-temporary-3",
        "after-replace-3",
        "after-registry",
        "after-lock-release",
        "after-temporary-2",
        "after-replace-2",
        "after-temporary-1",
        "after-replace-1",
        *_DISPOSAL_CHECKPOINTS,
    ),
}


@pytest.mark.parametrize("direction", ["forward", "back"])
def test_ac_0026_real_sigkill_at_each_recovery_write_checkpoint_converges(
    tmp_path: Path, direction: str
) -> None:
    """Killing recovery itself at any checkpoint leaves a state a retry finishes."""
    probe = tmp_path / "probe"
    probe.mkdir()
    _fixture(probe)
    _kill_rename(probe, _RECOVERY_START[direction])
    reached: list[str] = []
    probed = rename.recover_intent_rename(
        direction,
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=probe,
        _checkpoint=reached.append,
    )
    assert probed.status in {rename.RenameStatus.COMMITTED, rename.RenameStatus.ROLLED_BACK}
    assert tuple(dict.fromkeys(reached)) == _RECOVERY_CHECKPOINTS[direction]

    for index, checkpoint in enumerate(_RECOVERY_CHECKPOINTS[direction]):
        root = tmp_path / f"{index:02d}-{checkpoint}"
        root.mkdir()
        source_before = _fixture(root)
        before = _tree(root)
        _kill_rename(root, _RECOVERY_START[direction])

        _kill_recovery(root, direction, checkpoint)
        retried = _recover(root, direction)

        # A kill after the stage is removed leaves a finished operation, so the
        # retry finds nothing to recover; the tree must already be terminal.
        finished = (
            rename.RenameStatus.COMMITTED
            if direction == "forward"
            else rename.RenameStatus.ROLLED_BACK
        )
        if checkpoint == "after-stage-cleanup":
            assert retried.code == "recovery-missing", (checkpoint, retried)
        else:
            assert retried.status is finished, (checkpoint, retried)
        if direction == "forward":
            _assert_forward_terminal(root, source_before)
        else:
            _assert_back_terminal(root, before)
        _assert_no_recovery_residue(root)


def test_ac_0026_back_recovery_refuses_an_alien_successor_before_any_rollback(
    tmp_path: Path,
) -> None:
    """An extra link on the successor is refused before any other live file moves."""
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-registry")
    os.link(tmp_path / SUCCESSOR, tmp_path / "alien-successor-link")
    applied = _tree(tmp_path)

    result = _recover(tmp_path, "back")

    assert result.status is rename.RenameStatus.REFUSED
    assert _tree(tmp_path) == applied


def test_ac_0026_back_recovery_removes_the_successor_before_other_rollback(
    tmp_path: Path,
) -> None:
    """The successor leaves first, so a link raced in mid-rollback has nothing to attach to."""
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-registry")
    alien = tmp_path / "alien-successor-link"

    def link_successor_mid_rollback(checkpoint: str) -> None:
        if checkpoint == "before-registry" and (tmp_path / SUCCESSOR).exists():
            os.link(tmp_path / SUCCESSOR, alien)

    result = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
        _checkpoint=link_successor_mid_rollback,
    )

    assert result.status is rename.RenameStatus.ROLLED_BACK
    assert not alien.exists()
    assert _tree(tmp_path) == before


def test_t1_registry_write_reproves_lock_ownership_first(tmp_path: Path) -> None:
    """A lock swapped inside the critical section stops the write, recoverably."""
    _fixture(tmp_path)
    workspace = tmp_path / "workspace.toml"
    lock = tmp_path / ".workspace-repair.lock"
    registry_before = workspace.read_bytes()

    def swap_lock(checkpoint: str) -> None:
        # After the registry temporary is written, just before the live replace.
        if checkpoint == "after-temporary-3":
            lock.unlink()
            lock.write_bytes(b"1")

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=swap_lock,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert (result.status, result.code) == (rename.RenameStatus.PARTIAL, "lock-release-failed")
    assert workspace.read_bytes() == registry_before
    assert lock.read_bytes() == b"1"


def test_ac_0013_successor_name_staged_only_in_the_index_refuses_before_staging(
    tmp_path: Path,
) -> None:
    """Absent from the working tree is not enough; a name staged in the index is occupied.

    A name tracked at the base is already counted by the allocator, which then
    picks the next ordinal, so the index is the case that needs its own check.
    """
    _fixture(tmp_path)
    successor = rename.derive_successor_path(SOURCE, "STRAT", repository_root=tmp_path)
    (tmp_path / successor).write_text("occupied\n", encoding="utf-8")
    subprocess.run(["git", "add", successor], cwd=tmp_path, check=True)
    (tmp_path / successor).unlink()

    result = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert (result.status, result.code) == (rename.RenameStatus.REFUSED, "successor-exists")
    assert _stage_dirs(tmp_path) == []


def test_t1_bounded_read_refuses_a_link_added_while_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The allowed link state is proven on the descriptor at return, not only at open."""
    target = tmp_path / "target.md"
    target.write_bytes(b"x" * 10)
    alien = tmp_path / "alien-link"
    original_read = os.read

    def read_then_link(descriptor: int, size: int) -> bytes:
        if not alien.exists():
            os.link(target, alien)
        return original_read(descriptor, size)

    parent = os.open(tmp_path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        monkeypatch.setattr(rename.os, "read", read_then_link)
        with pytest.raises(ValueError, match="unsafe-file"):
            rename._read_at(parent, "target.md", max_bytes=100)
    finally:
        monkeypatch.undo()
        os.close(parent)
    assert target.stat().st_nlink == 2


def test_t1_recovery_refuses_alien_successor_link_before_destructive_act(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt_after_successor,
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    before = _tree(tmp_path)
    alien_bytes = (tmp_path / SUCCESSOR).read_bytes()
    (tmp_path / SUCCESSOR).unlink()
    (tmp_path / SUCCESSOR).write_bytes(alien_bytes)

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.code == "successor-conflict"
    after = _tree(tmp_path)
    assert after[SOURCE] == before[SOURCE]
    assert after["workspace.toml"] == before["workspace.toml"]


def test_t1_recovery_refuses_second_staged_link_while_successor_is_absent(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-seal"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    stage = _stage_dirs(tmp_path)[0]
    alien = tmp_path / "alien-successor-link"
    os.link(stage / "0000.postimage", alien)
    before = _tree(tmp_path)

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.code == "successor-conflict"
    assert not (tmp_path / SUCCESSOR).exists()
    after = _tree(tmp_path)
    assert after[SOURCE] == before[SOURCE]
    assert after["citation.md"] == before["citation.md"]
    assert after["workspace.toml"] == before["workspace.toml"]


def test_t1_forward_rechecks_staged_link_state_immediately_before_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-seal"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    stage = _stage_dirs(tmp_path)[0]
    before = _tree(tmp_path)
    remove_temporaries = rename._remove_temporaries

    def add_racing_link(root: Path, derived: Any) -> None:
        remove_temporaries(root, derived)
        os.link(stage / "0000.postimage", root / "racing-successor-link")

    monkeypatch.setattr(rename, "_remove_temporaries", add_racing_link)

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.code == "successor-conflict"
    assert not (tmp_path / SUCCESSOR).exists()
    after = _tree(tmp_path)
    assert after[SOURCE] == before[SOURCE]
    assert after["citation.md"] == before["citation.md"]
    assert after["workspace.toml"] == before["workspace.toml"]


def test_t1_incomplete_stage_rolls_back_and_cleanup_marker_finishes_forward(
    tmp_path: Path,
) -> None:
    back_root = tmp_path / "back"
    forward_root = tmp_path / "forward"
    back_root.mkdir()
    forward_root.mkdir()
    source_before = _fixture(back_root)
    _fixture(forward_root)

    partial_back = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=back_root,
        _checkpoint=_interrupt("after-seal"),
        _today=lambda: TOMBSTONE_DATE,
    )
    partial_forward = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=forward_root,
        _checkpoint=_interrupt("after-cleanup-marker"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial_back.status is rename.RenameStatus.PARTIAL
    assert partial_forward.status is rename.RenameStatus.PARTIAL

    back = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=back_root,
    )
    forward = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=forward_root,
    )

    assert back.status is rename.RenameStatus.ROLLED_BACK
    assert (back_root / SOURCE).read_bytes() == source_before
    assert not (back_root / SUCCESSOR).exists()
    assert forward.status is rename.RenameStatus.COMMITTED
    assert not _stage_payloads(back_root)
    assert not _stage_payloads(forward_root)


def test_t1_seal_is_last_and_record_is_comparison_only(tmp_path: Path) -> None:
    _fixture(tmp_path)
    checkpoints: list[str] = []

    def interrupt_after_seal(name: str) -> None:
        checkpoints.append(name)
        if name == "after-seal":
            raise rename.InjectedInterruption(name)

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=interrupt_after_seal,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.PARTIAL
    assert checkpoints == [
        "after-stage-created",
        "after-record",
        "after-postimage-0",
        "after-postimage-1",
        "after-postimage-2",
        "after-seal",
    ]
    stage = _stage_dirs(tmp_path)[0]
    assert {path.name for path in stage.iterdir()} == {
        "record.json",
        "0000.postimage",
        "0001.postimage",
        "0002.postimage",
        "complete.json",
    }
    record = json.loads((stage / "record.json").read_text(encoding="ascii"))
    assert set(record) == {
        "base_commit",
        "operation_id",
        "origin_view_sha256",
        "registry",
        "request",
        "version",
        "writes",
    }
    assert "bytes" not in record
    assert all(
        set(item)
        == {
            "action",
            "order",
            "path",
            "postimage_sha256",
            "preimage_sha256",
        }
        for item in record["writes"]
    )


def test_t1_unsealed_stage_discards_only_from_exact_all_before_state(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-record"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    stage = _stage_dirs(tmp_path)[0]
    assert {path.name for path in stage.iterdir()} == {"record.json"}

    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    assert stage.name in _SANDBOX_STAGE_REMOVALS


def test_t1_unsealed_stage_with_unknown_entry_is_never_swept(tmp_path: Path) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-record"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    stage = _stage_dirs(tmp_path)[0]
    unknown = stage / "unknown"
    unknown.write_bytes(b"keep")

    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.REFUSED
    assert unknown.read_bytes() == b"keep"


def test_t1_registry_reread_preserves_unrelated_concurrent_bytes(tmp_path: Path) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-seal"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    workspace = tmp_path / "workspace.toml"
    workspace.write_bytes(workspace.read_bytes() + b"\n# concurrent-owner-note\n")

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.COMMITTED
    result = workspace.read_bytes()
    assert b"# concurrent-owner-note" in result
    assert SOURCE.encode() not in result
    assert SUCCESSOR.encode() in result


def test_ac_0026_backward_registry_preserves_concurrent_successor_comment(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-lock-release"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    workspace = tmp_path / "workspace.toml"
    concurrent = f"\n# concurrent note keeps {SUCCESSOR}\n".encode()
    workspace.write_bytes(workspace.read_bytes() + concurrent)

    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    result = workspace.read_bytes()
    assert result.endswith(concurrent)
    assert result.count(SOURCE.encode()) == 1
    assert result.count(SUCCESSOR.encode()) == 1


def test_ac_0026_backward_registry_preserves_concurrent_nested_need(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-lock-release"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    workspace = tmp_path / "workspace.toml"
    concurrent = (
        "\n[concurrent]\n"
        'items = [{path = "unrelated", needs = '
        f'[{{type = "local", kind = "intent", path = "{SUCCESSOR}"}}]}}]\n'
    ).encode()
    workspace.write_bytes(workspace.read_bytes() + concurrent)

    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    result = workspace.read_bytes()
    assert result.endswith(concurrent)
    assert result.count(SOURCE.encode()) == 1
    assert result.count(SUCCESSOR.encode()) == 1


def test_ac_0026_backward_registry_refuses_ambiguous_same_line_edit_before_mutation(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-lock-release"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.status is rename.RenameStatus.PARTIAL
    workspace = tmp_path / "workspace.toml"
    current = workspace.read_bytes()
    workspace.write_bytes(
        current.replace(
            b"}]\n",
            f"}}] # ambiguous concurrent {SUCCESSOR}\n".encode(),
            1,
        )
    )
    before = _tree(tmp_path)

    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.REFUSED
    assert _tree(tmp_path) == before


def test_t1_operation_ids_are_opaque_and_duplicate_records_are_ambiguous(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    partial = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=_interrupt("after-seal"),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert partial.operation_id is not None
    assert re.fullmatch(r"[0-9a-f]{32}", partial.operation_id)
    original = _stage_dirs(tmp_path)[0]
    duplicate_id = "f" * 32 if partial.operation_id != "f" * 32 else "e" * 32
    duplicate = original.with_name(f".intent-rename-{duplicate_id}")
    shutil.copytree(original, duplicate)

    rerun = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert rerun.code == "recovery-ambiguous"


def test_t1_recovery_refuses_alien_lock_inode_without_unlinking_it(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _kill_rename(tmp_path, "after-lock-link")
    stage = _stage_dirs(tmp_path)[0]
    lock = tmp_path / ".workspace-repair.lock"
    lock.unlink()
    lock.write_bytes((stage / "lock.claim").read_bytes())
    before_inode = lock.stat().st_ino

    recovered = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.code == "lock-foreign"
    assert lock.stat().st_ino == before_inode


def test_t1_disposal_restarts_after_record_and_marker_removal(tmp_path: Path) -> None:
    for checkpoint in ("after-dispose-record", "after-dispose-cleanup"):
        root = tmp_path / checkpoint
        root.mkdir()
        _fixture(root)
        partial = rename.run_intent_rename(
            SOURCE,
            "STRAT",
            repository_root=root,
            _checkpoint=_interrupt(checkpoint),
            _today=lambda: TOMBSTONE_DATE,
        )
        assert partial.status is rename.RenameStatus.PARTIAL

        recovered = rename.recover_intent_rename(
            "forward",
            SOURCE,
            "STRAT",
            TOMBSTONE_DATE.isoformat(),
            repository_root=root,
        )

        assert recovered.status is rename.RenameStatus.COMMITTED
        assert not _stage_dirs(root)


@pytest.mark.parametrize(
    ("checkpoint", "direction", "terminal"),
    [
        ("after-stage-created", "back", "back"),
        ("after-record", "back", "back"),
        ("after-postimage-0", "back", "back"),
        ("after-postimage-1", "back", "back"),
        ("after-postimage-2", "back", "back"),
        ("after-seal", "forward", "forward"),
        ("after-successor", "back", "back"),
        ("after-temporary-1", "forward", "forward"),
        ("after-replace-1", "back", "back"),
        ("after-temporary-2", "forward", "forward"),
        ("after-replace-2", "back", "back"),
        ("after-lock-claim", "forward", "forward"),
        ("after-lock-link", "back", "back"),
        ("after-temporary-3", "forward", "forward"),
        ("after-replace-3", "back", "back"),
        ("after-registry", "forward", "forward"),
        ("after-lock-release", "back", "back"),
        ("after-terminal-validation", "forward", "forward"),
        ("after-cleanup-marker", "back", "forward"),
        ("after-dispose-postimage-0", "back", "forward"),
        ("after-dispose-postimage-1", "back", "forward"),
        ("after-dispose-postimage-2", "back", "forward"),
        ("after-dispose-seal", "back", "forward"),
        ("after-dispose-record", "back", "forward"),
        ("after-dispose-cleanup", "back", "forward"),
        # The opposite direction at every live-write checkpoint, so each one
        # proves both recovery directions reach a permitted end state.
        ("after-seal", "back", "back"),
        ("after-successor", "forward", "forward"),
        ("after-temporary-1", "back", "back"),
        ("after-replace-1", "forward", "forward"),
        ("after-temporary-2", "back", "back"),
        ("after-replace-2", "forward", "forward"),
        ("after-lock-claim", "back", "back"),
        ("after-lock-link", "forward", "forward"),
        ("after-temporary-3", "back", "back"),
        ("after-replace-3", "forward", "forward"),
        ("after-registry", "back", "back"),
        ("after-lock-release", "forward", "forward"),
        ("after-terminal-validation", "back", "back"),
    ],
    ids=lambda value: value,
)
def test_ac_0026_real_sigkill_at_each_rename_write_checkpoint_recovers(
    tmp_path: Path,
    checkpoint: str,
    direction: str,
    terminal: str,
) -> None:
    source_before = _fixture(tmp_path)
    before = _tree(tmp_path)

    _kill_rename(tmp_path, checkpoint)
    recovered = rename.recover_intent_rename(
        direction,
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    if terminal == "forward":
        assert recovered.status is rename.RenameStatus.COMMITTED
        _assert_forward_terminal(tmp_path, source_before)
    else:
        assert recovered.status is rename.RenameStatus.ROLLED_BACK
        _assert_back_terminal(tmp_path, before)


def test_ac_0026_real_sigkill_after_successor_removal_recovers_back(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    before = _tree(tmp_path)
    _kill_rename(tmp_path, "after-successor")

    _kill_recovery(tmp_path, "back", "after-successor-remove")
    recovered = rename.recover_intent_rename(
        "back",
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=tmp_path,
    )

    assert recovered.status is rename.RenameStatus.ROLLED_BACK
    _assert_back_terminal(tmp_path, before)


def test_ac_0026_real_sigkill_after_stage_cleanup_is_already_forward_complete(
    tmp_path: Path,
) -> None:
    source_before = _fixture(tmp_path)

    _kill_operator(
        tmp_path,
        ["rename", SOURCE, "STRAT"],
        "after-stage-cleanup",
        sandbox_cleanup=True,
    )

    _assert_forward_terminal(tmp_path, source_before)
    disposed = list(
        (tmp_path / "docs/product/intents").glob(
            ".sandbox-disposed-.intent-rename-*"
        )
    )
    assert len(disposed) == 1
    assert list(disposed[0].iterdir()) == []
