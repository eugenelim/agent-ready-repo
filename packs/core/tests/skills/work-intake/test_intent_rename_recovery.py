# STUB: AC-0026
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-rename-test.md"
TOMBSTONE_DATE = date(2026, 9, 29)
HOSTILE = "HOSTILE-CONTENT-SHOULD-NOT-ECHO"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location(
        "core_work_intake_intent_rename_recovery", SCRIPT
    )
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()

_SANDBOX_STAGE_REMOVALS: list[str] = []


def _sandbox_remove_empty_stage(parent_descriptor: int, name: str) -> None:
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
    _SANDBOX_STAGE_REMOVALS.append(name)


rename._remove_empty_stage = _sandbox_remove_empty_stage


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
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)


def _fixture(root: Path) -> bytes:
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
    (root / "workspace.toml").write_text(
        "[backlog]\n"
        f'open = [{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}]\n',
        encoding="utf-8",
    )
    _commit(root)
    return source_bytes


def _install_origin_only_name(root: Path, name: str) -> None:
    """Expose one higher ordinal only through a local origin-tracking ref."""
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "switch", "-c", "remote-seed"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "docs/product/intents" / name).write_text(
        "- **Slug:** `remote-only`\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "remote fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    remote_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "switch", "--detach", base],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "."],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", remote_commit],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _interrupt(name: str) -> Callable[[str], None]:
    def checkpoint(checkpoint_name: str) -> None:
        if checkpoint_name == name:
            raise rename.InjectedInterruption(checkpoint_name)

    return checkpoint


def _stage(root: Path) -> Path:
    stages = [
        stage
        for stage in (root / "docs/product/intents").glob(".intent-rename-*")
        if stage.name not in _SANDBOX_STAGE_REMOVALS
    ]
    assert len(stages) == 1
    return stages[0]


def _sealed_stage(root: Path, checkpoint: str = "after-seal") -> Path:
    _fixture(root)
    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=root,
        _checkpoint=_interrupt(checkpoint),
        _today=lambda: TOMBSTONE_DATE,
    )
    assert result.status is rename.RenameStatus.PARTIAL
    return _stage(root)


# Drives the operator's real CLI `main` with an in-process checkpoint that
# SIGKILLs the process; the installed entry point exposes no such seam.
_KILL_CHILD = """
import datetime
import importlib.util
import os
import signal
import sys
from pathlib import Path

script, checkpoint, today = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
spec = importlib.util.spec_from_file_location(
    "core_work_intake_intent_rename_kill_child", script
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def kill_at(name):
    if name == checkpoint:
        os.kill(os.getpid(), signal.SIGKILL)

raise SystemExit(
    module.main(
        sys.argv[4:],
        _checkpoint=kill_at,
        _today=lambda: datetime.date.fromisoformat(today),
    )
)
"""


def _kill_rename_after_seal(root: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            _KILL_CHILD,
            os.fspath(SCRIPT),
            "after-seal",
            TOMBSTONE_DATE.isoformat(),
            "rename",
            SOURCE,
            "STRAT",
        ],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    assert result.returncode == -signal.SIGKILL, result


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def _recover(root: Path, direction: str = "forward") -> Any:
    return rename.recover_intent_rename(
        direction,
        SOURCE,
        "STRAT",
        TOMBSTONE_DATE.isoformat(),
        repository_root=root,
    )


def _assert_refuses_without_live_mutation(root: Path, before: dict[str, bytes]) -> None:
    result = _recover(root)
    assert result.status is rename.RenameStatus.REFUSED
    after = _tree(root)
    for relative, data in before.items():
        if "/.intent-rename-" not in relative:
            assert after[relative] == data


def _rewrite_record(stage: Path, update: Callable[[dict[str, Any]], None]) -> None:
    record = json.loads((stage / "record.json").read_text(encoding="ascii"))
    update(record)
    (stage / "record.json").write_text(
        json.dumps(record, allow_nan=False, sort_keys=True, separators=(",", ":")),
        encoding="ascii",
    )


def _rewrite_seal(stage: Path) -> None:
    record = (stage / "record.json").read_bytes()
    seal = json.loads((stage / "complete.json").read_text(encoding="ascii"))
    seal["record_sha256"] = rename._sha256(record)
    seal["postimage_sha256"] = [
        rename._sha256((stage / "0000.postimage").read_bytes()),
        rename._sha256((stage / "0001.postimage").read_bytes()),
    ]
    (stage / "complete.json").write_text(
        json.dumps(seal, allow_nan=False, sort_keys=True, separators=(",", ":")),
        encoding="ascii",
    )


def test_t2_record_parser_rejects_closed_schema_and_structural_attacks(
    tmp_path: Path,
) -> None:
    cases: list[tuple[str, Callable[[Path], None]]] = [
        ("truncated", lambda stage: (stage / "record.json").write_bytes(b'{"request":')),
        (
            "duplicate",
            lambda stage: (stage / "record.json").write_bytes(
                (stage / "record.json").read_bytes().replace(b'"version":1', b'"version":1,"version":1', 1)
            ),
        ),
        ("unknown", lambda stage: _rewrite_record(stage, lambda record: record.update({"extra": HOSTILE}))),
        ("wrong-type", lambda stage: _rewrite_record(stage, lambda record: record.update({"writes": HOSTILE}))),
        ("deep", lambda stage: (stage / "record.json").write_bytes((b'{"x":' * 80) + b'0' + (b"}" * 80))),
        ("members", lambda stage: (stage / "record.json").write_bytes(b"{" + b",".join(f'"k{i}":0'.encode() for i in range(5000)) + b"}")),
        ("string", lambda stage: _rewrite_record(stage, lambda record: record["request"].update({"source": "x" * 5000}))),
        ("nonfinite", lambda stage: (stage / "record.json").write_bytes(b'{"request":{"source":"docs/product/intents/FEAT-0001-rename-test.md","target_token":"STRAT","date":"2026-09-29"},"version":NaN}')),
    ]
    for name, mutate in cases:
        root = tmp_path / name
        root.mkdir()
        stage = _sealed_stage(root)
        before = _tree(root)
        mutate(stage)

        _assert_refuses_without_live_mutation(root, before)


def test_t2_decoder_recursion_error_is_a_fixed_refusal(tmp_path: Path) -> None:
    stage = _sealed_stage(tmp_path)
    before = _tree(tmp_path)
    (stage / "record.json").write_bytes((b"[" * 12000) + b"0" + (b"]" * 12000))

    _assert_refuses_without_live_mutation(tmp_path, before)


def test_t2_recomputed_record_or_postimage_changes_do_not_gain_authority(
    tmp_path: Path,
) -> None:
    for name, mutate in {
        "record": lambda stage: (
            _rewrite_record(
                stage,
                lambda record: record["registry"].update(
                    {"successor": "docs/product/intents/STRAT-9999-hostile.md"}
                ),
            ),
            _rewrite_seal(stage),
        ),
        "origin-view": lambda stage: (
            _rewrite_record(
                stage,
                lambda record: record.update({"origin_view_sha256": "0" * 64}),
            ),
            _rewrite_seal(stage),
        ),
        "postimage": lambda stage: (
            (stage / "0001.postimage").write_bytes(b"# hostile\n"),
            _rewrite_seal(stage),
        ),
        # `True == 1` and `False == 0` in Python, so these substitutions would
        # pass a value comparison against the re-derived record.
        "boolean-version": lambda stage: (
            _rewrite_record(stage, lambda record: record.update({"version": True})),
            _rewrite_seal(stage),
        ),
        "boolean-order": lambda stage: (
            _rewrite_record(
                stage,
                lambda record: [
                    item.update({"order": bool(item["order"])})
                    for item in record["writes"]
                    if item["order"] in (0, 1)
                ],
            ),
            _rewrite_seal(stage),
        ),
    }.items():
        root = tmp_path / name
        root.mkdir()
        stage = _sealed_stage(root)
        before = _tree(root)
        mutate(stage)

        _assert_refuses_without_live_mutation(root, before)


def test_t2_recovery_rederives_the_stable_pinned_origin_union(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _install_origin_only_name(tmp_path, "STRAT-0009-remote-only.md")
    _kill_rename_after_seal(tmp_path)

    result = _recover(tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED
    assert (tmp_path / "docs/product/intents/STRAT-0010-rename-test.md").is_file()


def test_t2_recovery_refuses_before_mutation_when_origin_view_changed(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _install_origin_only_name(tmp_path, "STRAT-0009-remote-only.md")
    _kill_rename_after_seal(tmp_path)
    before = _tree(tmp_path)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    result = _recover(tmp_path)

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "base-changed"
    assert _tree(tmp_path) == before


def test_t2_parent_symlink_swap_refuses_before_mutation(tmp_path: Path) -> None:
    donor = tmp_path / "donor"
    attack = tmp_path / "attack"
    donor.mkdir()
    stage = _sealed_stage(donor)
    attack.mkdir()
    shutil.copytree(donor / ".git", attack / ".git")
    shutil.copy2(donor / "workspace.toml", attack / "workspace.toml")
    (attack / "docs/product").mkdir(parents=True)
    held = attack / "held-intents"
    shutil.copytree(donor / "docs/product/intents", held)
    (attack / "docs/product/intents").symlink_to("../../held-intents", target_is_directory=True)
    before = _tree(attack)

    result = _recover(attack)

    assert result.status is rename.RenameStatus.REFUSED
    assert (held / stage.name / "record.json").read_bytes() == before[
        f"held-intents/{stage.name}/record.json"
    ]
    assert not (attack / SUCCESSOR).exists()


def test_t2_owned_successor_is_accepted_but_foreign_identical_inode_refuses(
    tmp_path: Path,
) -> None:
    owned = tmp_path / "owned"
    foreign = tmp_path / "foreign"
    owned.mkdir()
    foreign.mkdir()
    _sealed_stage(owned, "after-successor")
    foreign_stage = _sealed_stage(foreign, "after-successor")
    (foreign / SUCCESSOR).unlink()
    (foreign / SUCCESSOR).write_bytes((foreign_stage / "0000.postimage").read_bytes())
    before = _tree(foreign)

    assert _recover(owned).status is rename.RenameStatus.COMMITTED
    assert (owned / SUCCESSOR).exists()
    _assert_refuses_without_live_mutation(foreign, before)
    assert (foreign / SUCCESSOR).stat().st_ino != (foreign_stage / "0000.postimage").stat().st_ino


def test_t2_lock_claim_identity_and_pid_are_validated_before_mutation(tmp_path: Path) -> None:
    cases: dict[str, Callable[[Path, Path], None]] = {}

    def malformed(root: Path, stage: Path) -> None:
        (stage / "lock.claim").write_bytes(b"not-a-pid")

    def live(root: Path, stage: Path) -> None:
        (stage / "lock.claim").write_text(str(os.getpid()), encoding="ascii")

    def foreign_inode(root: Path, stage: Path) -> None:
        lock = root / ".workspace-repair.lock"
        lock.unlink()
        lock.write_bytes((stage / "lock.claim").read_bytes())

    def out_of_range(root: Path, stage: Path) -> None:
        # Matches the digit shape but exceeds `pid_t`; `os.kill` would overflow.
        (stage / "lock.claim").write_bytes(b"99999999999999999999")

    cases["malformed"] = malformed
    cases["out-of-range"] = out_of_range
    cases["live"] = live
    cases["foreign-inode"] = foreign_inode

    for name, mutate in cases.items():
        root = tmp_path / name
        root.mkdir()
        stage = _sealed_stage(root, "after-lock-link")
        mutate(root, stage)
        before = _tree(root)

        _assert_refuses_without_live_mutation(root, before)
        assert (root / ".workspace-repair.lock").exists()


@pytest.mark.parametrize(
    ("source", "token", "code"),
    [
        ("README.md", "STRAT", "source-outside-root"),
        ("docs/product/intents/../../README.md", "STRAT", "source-outside-root"),
        (SOURCE, "NOT-A-TOKEN", "token-unknown"),
    ],
)
def test_t2_recovery_confines_the_request_before_reading_any_stage(
    tmp_path: Path, source: str, token: str, code: str
) -> None:
    _sealed_stage(tmp_path)
    (tmp_path / "README.md").write_text(f"Cites {SOURCE}.\n", encoding="utf-8")
    before = _tree(tmp_path)

    result = rename.recover_intent_rename(
        "forward", source, token, TOMBSTONE_DATE.isoformat(), repository_root=tmp_path
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == code
    assert _tree(tmp_path) == before


@pytest.mark.parametrize("variable", ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"])
def test_t2_redirected_git_environment_refuses_rename_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    _sealed_stage(tmp_path)
    before = _tree(tmp_path)
    monkeypatch.setenv(variable, os.fspath(tmp_path / "elsewhere"))

    renamed = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)
    recovered = _recover(tmp_path)

    assert (renamed.code, recovered.code) == (
        "git-environment-redirected",
        "git-environment-redirected",
    )
    assert _tree(tmp_path) == before


def test_t2_git_reads_are_bound_to_the_established_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inherited Git variables cannot swap the index the snapshot is read from."""
    _sealed_stage(tmp_path)
    expected = rename._tracked_paths(tmp_path)
    assert expected
    monkeypatch.setenv("GIT_INDEX_FILE", os.fspath(tmp_path / "empty.index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", os.fspath(tmp_path / "elsewhere"))

    assert rename._tracked_paths(tmp_path) == expected


def _finishes_within(seconds: float, call: Callable[[], object]) -> list[object]:
    """Run ``call`` on a daemon thread and report its outcome if it returns in time."""
    outcome: list[object] = []

    def target() -> None:
        try:
            outcome.append(call())
        except Exception as error:  # noqa: BLE001 - the outcome is asserted
            outcome.append(error)

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(seconds)
    assert not worker.is_alive(), "read blocked on a special file"
    return outcome


def test_t2_special_file_targets_refuse_without_blocking(tmp_path: Path) -> None:
    """A FIFO in place of a staged file or tombstone target cannot hang a read."""
    os.mkfifo(tmp_path / "pipe")
    parent = os.open(tmp_path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        (outcome,) = _finishes_within(5, lambda: rename._read_at(parent, "pipe", max_bytes=10))
    finally:
        os.close(parent)
    assert isinstance(outcome, ValueError)

    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    (tmp_path / old).parent.mkdir(parents=True)
    (tmp_path / old).write_text(
        "# Tombstone: old\n\n- **Slug:** `old`\n- **Tombstone:** 2026-09-29\n"
        f"- **Reissued as:** {target}\n",
        encoding="utf-8",
    )
    os.mkfifo(tmp_path / target)
    (resolved,) = _finishes_within(
        5, lambda: rename.resolve_intent_path(old, repository_root=tmp_path)
    )
    assert resolved.code == "tombstone-target-refused"


def test_t2_directory_caps_apply_while_entries_are_enumerated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stage listings never materialize a whole directory before the cap fires."""
    for index in range(6):
        (tmp_path / f"entry-{index}").write_bytes(b"")

    def no_listdir(*_args: object) -> list[str]:
        raise AssertionError("os.listdir materializes the whole directory")

    monkeypatch.setattr(rename.os, "listdir", no_listdir)
    parent = os.open(tmp_path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        assert len(rename._list_at(parent)) == 6
        monkeypatch.setattr(rename, "_MAX_STAGE_ENTRIES", 5)
        with pytest.raises(ValueError, match="stage-entry-bound"):
            rename._list_at(parent)
    finally:
        os.close(parent)


def test_t2_missing_no_follow_semantics_refuse_before_any_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without descriptor-relative no-follow calls, nothing runs on following flags."""
    _sealed_stage(tmp_path)
    before = _tree(tmp_path)
    monkeypatch.setattr(rename.os, "supports_dir_fd", set())

    renamed = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)
    recovered = _recover(tmp_path)
    resolved = rename.resolve_intent_path(SOURCE, repository_root=tmp_path)

    assert (renamed.code, recovered.code) == ("filesystem-unsupported", "filesystem-unsupported")
    assert resolved.code == "resolve-refused"
    assert _tree(tmp_path) == before


def test_t2_stale_lock_is_reproven_immediately_before_it_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lock another writer takes after the dead-owner check is refused, not removed."""
    stage = _sealed_stage(tmp_path, "after-lock-link")
    lock = tmp_path / ".workspace-repair.lock"
    # The claim and the lock are one inode; give it an owner that has exited.
    exited = subprocess.Popen([sys.executable, "-c", "pass"])
    exited.wait()
    (stage / "lock.claim").write_bytes(str(exited.pid).encode("ascii"))
    assert lock.read_bytes() == str(exited.pid).encode("ascii")
    original = rename._pid_is_dead

    def dead_then_replaced(payload: bytes) -> bool:
        result = original(payload)
        if not getattr(dead_then_replaced, "swapped", False):
            dead_then_replaced.swapped = True  # type: ignore[attr-defined]
            lock.unlink()
            lock.write_bytes(str(os.getpid()).encode("ascii"))
        return result

    monkeypatch.setattr(rename, "_pid_is_dead", dead_then_replaced)

    result = _recover(tmp_path)

    assert getattr(dead_then_replaced, "swapped", False)
    assert result.status is rename.RenameStatus.REFUSED
    assert lock.read_bytes() == str(os.getpid()).encode("ascii")


def test_t2_dirty_check_ignores_injected_git_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Injected Git configuration changes neither answer of the dirty check."""
    _sealed_stage(tmp_path)
    assert rename._paths_dirty(tmp_path, [SOURCE]) is False
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", os.fspath(tmp_path / "does-not-exist"))

    assert rename._paths_dirty(tmp_path, [SOURCE]) is False
    (tmp_path / SOURCE).write_text("Uncommitted edit.\n", encoding="utf-8")
    assert rename._paths_dirty(tmp_path, [SOURCE]) is True


def test_t2_symlink_loop_during_confinement_is_a_fixed_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Python 3.11 and 3.12 report a symlink loop as RuntimeError; it refuses, never raises."""
    _sealed_stage(tmp_path)
    before = _tree(tmp_path)

    def loop(**_kwargs: object) -> Path:
        raise RuntimeError("Symlink loop from 'docs/product/intents/loop'")

    monkeypatch.setattr(rename._request._transaction, "resolve_confined_target", loop)

    resolved = rename.resolve_intent_path(SOURCE, repository_root=tmp_path)
    recovered = _recover(tmp_path)

    assert resolved.code == "resolve-refused"
    assert (recovered.status, recovered.code) == (
        rename.RenameStatus.REFUSED,
        "source-outside-root",
    )
    assert _tree(tmp_path) == before


def test_t2_changed_head_and_operator_date_disagreement_refuse_before_mutation(
    tmp_path: Path,
) -> None:
    changed_head = tmp_path / "changed-head"
    changed_head.mkdir()
    _sealed_stage(changed_head)
    (changed_head / "new-file.md").write_text("new head\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=changed_head, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "move head"], cwd=changed_head, check=True, capture_output=True
    )
    before_head = _tree(changed_head)
    _assert_refuses_without_live_mutation(changed_head, before_head)

    date_root = tmp_path / "date"
    date_root.mkdir()
    _sealed_stage(date_root)
    before_date = _tree(date_root)
    result = rename.recover_intent_rename(
        "forward",
        SOURCE,
        "STRAT",
        "2026-09-30",
        repository_root=date_root,
    )
    assert result.status is rename.RenameStatus.REFUSED
    assert _tree(date_root) == before_date


def test_t2_stage_entry_and_byte_budgets_refuse_before_mutation(tmp_path: Path) -> None:
    for name, mutate in {
        "entries": lambda stage: [
            (stage / f"extra-{index}").write_bytes(b"x") for index in range(1100)
        ],
        "record-bytes": lambda stage: (stage / "record.json").write_bytes(b"{" + b'"x":' + (b'"y"' * (256 * 1024)) + b"}"),
        "postimage-bytes": lambda stage: (stage / "0001.postimage").write_bytes(b"x" * (4 * 1024 * 1024 + 1)),
    }.items():
        root = tmp_path / name
        root.mkdir()
        stage = _sealed_stage(root)
        before = _tree(root)
        mutate(stage)

        _assert_refuses_without_live_mutation(root, before)


def test_t2_no_seal_and_cleanup_marker_are_terminal_state_limited(tmp_path: Path) -> None:
    no_seal = tmp_path / "no-seal"
    no_seal.mkdir()
    no_seal_stage = _sealed_stage(no_seal, "after-record")
    (no_seal / SOURCE).write_text("alien\n", encoding="utf-8")
    no_seal_before = _tree(no_seal)
    result = _recover(no_seal, "back")
    assert result.status is rename.RenameStatus.REFUSED
    assert (no_seal_stage / "record.json").exists()
    assert _tree(no_seal) == no_seal_before

    cleanup = tmp_path / "cleanup"
    cleanup.mkdir()
    cleanup_stage = _sealed_stage(cleanup, "after-cleanup-marker")
    (cleanup / SOURCE).write_text("alien\n", encoding="utf-8")
    cleanup_before = _tree(cleanup)
    result = _recover(cleanup)
    assert result.status is rename.RenameStatus.REFUSED
    assert (cleanup_stage / "cleanup.json").exists()
    assert _tree(cleanup) == cleanup_before


def test_t2_fixed_cli_diagnostics_do_not_echo_hostile_record_content(tmp_path: Path) -> None:
    stage = _sealed_stage(tmp_path)
    _rewrite_record(stage, lambda record: record.update({"extra": HOSTILE}))
    result = subprocess.run(
        [
            sys.executable,
            os.fspath(SCRIPT),
            "recover",
            "forward",
            SOURCE,
            "STRAT",
            TOMBSTONE_DATE.isoformat(),
        ],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert HOSTILE.encode() not in result.stdout
    assert HOSTILE.encode() not in result.stderr
