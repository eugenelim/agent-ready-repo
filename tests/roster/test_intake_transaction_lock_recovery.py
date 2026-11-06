"""Roster coverage for the intake transaction's workspace-lock recovery.

Spec: ``docs/specs/work-item-promotion-handoff`` — task T22 (AC-0028). The
shared `_acquire_workspace_lock` gains stale-owner recovery — liveness
probe, identity re-verification immediately before the removal, one
acquisition retry — and atomic publication: a pid-complete temporary,
unique to its holder, linked into place. A lock whose owner is alive, or
whose payload carries no parseable pid, is never taken; a non-regular file
at the lock path is never probed and never removed. Every
`run_intake_transaction` caller gains the recovery.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-intake" / "scripts"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


IT = _load_module("_roster_intake_transaction_locks", SCRIPTS_DIR / "intake_transaction.py")

LOCK_NAME = IT.WORKSPACE_LOCK_FILE


def _git_repo(base: Path, name: str) -> Path:
    repo = base / name
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    (repo / "docs").mkdir(parents=True)
    return repo


def _dead_pid() -> int:
    """A pid that no longer exists: a short-lived child that already exited."""
    child = subprocess.Popen(["/usr/bin/true"])
    child.wait()
    assert child.returncode == 0
    return child.pid


def _write_lock(repo: Path, payload: bytes) -> None:
    (repo / LOCK_NAME).write_bytes(payload)


def _committed(repo: Path) -> Any:
    """One transaction over the prepared repo; its result."""
    return IT.run_intake_transaction(
        repository_root=repo,
        configured_parent="docs",
        artifact_target="docs/artifact.md",
        materialize_artifact=lambda confined: confined.write_text("artifact", encoding="utf-8"),
        rollback_partial_state=lambda: None,
        record_reconciliation=lambda message: None,
        dispatch_processor=lambda: None,
    )


def test_dead_owner_lock_is_recovered_and_the_transaction_completes(
    tmp_path: Path,
) -> None:
    # AC-0028: a workspace lock holding a pid that no longer exists is
    # recovered — probe, re-verify, remove, one retry — and the transaction
    # completes, where the same state previously returned LOCK_BUSY forever.
    repo = _git_repo(tmp_path, "dead-owner")
    _write_lock(repo, str(_dead_pid()).encode("ascii"))

    result = _committed(repo)

    assert result.status.name == "COMMITTED", result
    assert (repo / "docs" / "artifact.md").read_text(encoding="utf-8") == "artifact"
    # The transaction's own lock was released on completion.
    assert not (repo / LOCK_NAME).exists()


def test_live_owner_lock_is_never_taken(tmp_path: Path) -> None:
    # AC-0028: a workspace lock holding the running process's own pid —
    # provably live — is refused, never removed.
    repo = _git_repo(tmp_path, "live-owner")
    _write_lock(repo, str(os.getpid()).encode("ascii"))

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", result
    assert (repo / LOCK_NAME).read_bytes() == str(os.getpid()).encode("ascii")


def test_lock_owned_by_another_live_process_is_treated_as_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # AC-0028: a probe that raises PermissionError — the pid exists but
    # belongs to another user — treats the owner as live and refuses.
    repo = _git_repo(tmp_path, "foreign-live-owner")
    _write_lock(repo, str(_dead_pid()).encode("ascii"))

    def refusing_probe(pid: int, signal: int) -> None:
        raise PermissionError(pid, "exists but owned by another user")

    monkeypatch.setattr(os, "kill", refusing_probe)

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", result
    assert (repo / LOCK_NAME).exists()


def test_pidless_lock_payload_is_never_removed(tmp_path: Path) -> None:
    # AC-0028: a lock whose payload carries no parseable pid is treated as
    # a live owner and never removed.
    for payload in (b"", b"not-a-pid", b"0", b"-1"):
        repo = _git_repo(tmp_path, f"pidless-{payload!r}")
        _write_lock(repo, payload)

        result = _committed(repo)

        assert result.status.name == "LOCK_BUSY", payload
        assert (repo / LOCK_NAME).read_bytes() == payload


@pytest.mark.parametrize("alien", ["symlink", "fifo"])
def test_alien_file_at_the_lock_path_is_never_probed_or_removed(
    tmp_path: Path, alien: str
) -> None:
    # AC-0028: a non-regular file at the lock path — a symlink or a FIFO —
    # is alien: never probed, never removed, and the transaction stays
    # lock-busy. The payload read is no-follow, so the symlink target is
    # never opened.
    repo = _git_repo(tmp_path, f"alien-{alien}")
    outside = tmp_path / "outside-target.txt"
    outside.write_text("outside the repository", encoding="utf-8")
    lock_path = repo / LOCK_NAME
    if alien == "symlink":
        lock_path.symlink_to(outside)
    else:
        os.mkfifo(lock_path)

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", alien
    # The alien file itself is untouched.
    if alien == "symlink":
        assert lock_path.is_symlink()
    else:
        import stat as stat_module

        assert stat_module.S_ISFIFO(lock_path.stat().st_mode)
    assert outside.read_text(encoding="utf-8") == "outside the repository"


def test_a_lock_replaced_between_probe_and_removal_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # AC-0028, the concurrent-recovery race: a fresh lock taken at the
    # same path between the probe and the removal is refused, not removed
    # — the re-verification sees a different inode or payload and returns
    # lock-busy.
    repo = _git_repo(tmp_path, "race")
    _write_lock(repo, str(_dead_pid()).encode("ascii"))
    original_probe = IT._pid_is_live
    raced = {"done": False}

    def racing_probe(pid: int) -> bool:
        # Between the liveness probe and the re-verification, another
        # writer removes the stale lock and takes a fresh live one.
        if not raced["done"]:
            raced["done"] = True
            (repo / LOCK_NAME).unlink()
            _write_lock(repo, str(os.getpid()).encode("ascii"))
        return original_probe(pid)

    monkeypatch.setattr(IT, "_pid_is_live", racing_probe)

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", result
    # The fresh lock was not removed.
    assert (repo / LOCK_NAME).read_bytes() == str(os.getpid()).encode("ascii")


def test_acquisition_publishes_the_lock_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # AC-0028: the lock never exists without its pid. A link step that
    # fails leaves no lock at the lock path, and the pid-complete temporary
    # is unlinked on failure — never left behind as a lock.
    repo = _git_repo(tmp_path, "atomic")
    unlinked_temps: list[str] = []
    original_link = os.link

    def failing_link(src: Any, dst: Any, **kwargs: Any) -> None:
        assert str(dst).endswith(LOCK_NAME)
        unlinked_temps.append(Path(str(src)).name)
        raise OSError("injected link failure")

    monkeypatch.setattr(os, "link", failing_link)

    with pytest.raises(OSError, match="injected link failure"):
        IT._acquire_workspace_lock(repo)

    assert not (repo / LOCK_NAME).exists()
    assert list(repo.glob(f"{LOCK_NAME}.*")) == []
    assert len(unlinked_temps) == 1
    # The temporary's name is unique to its holder: the owner's pid plus a
    # random token, so concurrent acquirers never collide.
    name = unlinked_temps[0]
    assert name.startswith(f"{LOCK_NAME}.{os.getpid()}."), name
    assert name.endswith(".tmp"), name

    # After the failure, a plain acquisition succeeds — the injected
    # failure leaves no residue.
    monkeypatch.setattr(os, "link", original_link)
    lock_path = IT._acquire_workspace_lock(repo)
    assert lock_path == repo / LOCK_NAME
    assert (repo / LOCK_NAME).read_bytes() == str(os.getpid()).encode("ascii")
    # The temporary is unlinked immediately after publication.
    assert list(repo.glob(f"{LOCK_NAME}.*")) == []
    (repo / LOCK_NAME).unlink()


def test_orphaned_temporary_never_blocks_a_later_acquisition(tmp_path: Path) -> None:
    # AC-0028: an orphaned acquisition temporary — a killed creator's
    # residue — is inert garbage. A later acquisition never collides with
    # it and never treats it as a lock.
    repo = _git_repo(tmp_path, "orphan")
    orphan = repo / f"{LOCK_NAME}.999999.deadbeefdeadbeef.tmp"
    orphan.write_bytes(b"999999")

    lock_path = IT._acquire_workspace_lock(repo)

    assert lock_path == repo / LOCK_NAME
    assert (repo / LOCK_NAME).read_bytes() == str(os.getpid()).encode("ascii")
    # The orphan was neither removed nor consulted.
    assert orphan.exists()
    (repo / LOCK_NAME).unlink()


def test_skill_section_5_records_the_lock_recovery_and_its_limits() -> None:
    # § D1 (AC-0028): work-intake's § 5 states the stale-owner recovery and
    # its limits — dead owner removed after identity re-verification; live
    # and pid-less locks never taken or removed; alien non-regular files at
    # the lock path never probed or removed.
    skill = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-intake" / "SKILL.md"
    sections: dict[str, str] = {}
    current = ""
    for line in skill.read_text(encoding="utf-8").splitlines():
        if line.startswith("### ") and ". " in line:
            current = line.split(".", 1)[0].removeprefix("### ").strip()
            sections[current] = line
        elif current:
            sections[current] += "\n" + line
    section = " ".join(sections["5"].split())
    assert "a lock left by a process that no longer exists is stale" in section
    assert "liveness probe" in section
    assert "identity re-verification" in section
    assert "never taken or removed" in section
    assert "never probed and never removed" in section
    assert "publishes the lock atomically" in section


def test_unprobeable_numeric_pid_holds_as_live(tmp_path: Path) -> None:
    # AC-0028 (T24, finding adv-hardening-001): a lock payload that is an
    # all-digit pid above INT32_MAX — one os.kill cannot address — is
    # unprobeable, and unprobeable means live: the transaction returns
    # lock-busy, the lock is never removed, and no exception escapes
    # run_intake_transaction to abort the drain run.
    repo = _git_repo(tmp_path, "unprobeable-pid")
    _write_lock(repo, str(2**31).encode("ascii"))

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", result
    assert (repo / LOCK_NAME).read_bytes() == str(2**31).encode("ascii")


def test_lock_identity_opens_without_the_posix_follow_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # PR #1705 review: `O_NOFOLLOW` and `O_NONBLOCK` do not exist on
    # Windows; the identity read must still open the lock when the flags
    # are absent, refusing aliens through the regular-file and identity
    # comparisons alone.
    repo = _git_repo(tmp_path, "no-posix-flags")
    _write_lock(repo, str(os.getpid()).encode("ascii"))
    monkeypatch.delattr(os, "O_NOFOLLOW")
    monkeypatch.delattr(os, "O_NONBLOCK")

    identity = IT._lock_identity(repo)

    assert identity is not None
    assert identity[1] == str(os.getpid()).encode("ascii")


def test_pid_is_live_on_windows_treats_every_pid_as_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # PR #1705 review: Windows has no signal-0 probe — `os.kill` there
    # terminates the target — so on Windows every pid is live and the
    # probe is never reached.
    def poisoning_probe(pid: int, signal: int) -> None:
        raise AssertionError("os.kill must not be called on win32")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(os, "kill", poisoning_probe)

    assert IT._pid_is_live(1_234_567) is True


def test_windows_busy_lock_returns_lock_busy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # PR #1705 review: end to end on the win32 platform path — a busy lock
    # must return LOCK_BUSY, not crash on the missing flags or probe the
    # owner.
    repo = _git_repo(tmp_path, "win32-busy")
    _write_lock(repo, str(os.getpid()).encode("ascii"))

    def poisoning_probe(pid: int, signal: int) -> None:
        raise AssertionError("os.kill must not be called on win32")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(os, "kill", poisoning_probe)

    result = _committed(repo)

    assert result.status.name == "LOCK_BUSY", result
    assert (repo / LOCK_NAME).read_bytes() == str(os.getpid()).encode("ascii")


def test_publication_survives_a_failed_temporary_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # PR #1705 review: a failure to sweep the inert temporary after the
    # lock is published — antivirus or file-sharing interference — never
    # fails an acquisition that already succeeded.
    repo = _git_repo(tmp_path, "sweep-failure")
    real_unlink = os.unlink

    def refusing_sweep(path: Any, **kwargs: Any) -> Any:
        if str(path).endswith(".tmp"):
            raise OSError("simulated antivirus interference")
        return real_unlink(path, **kwargs)

    monkeypatch.setattr(os, "unlink", refusing_sweep)

    result = _committed(repo)

    assert result.status.name == "COMMITTED", result
    assert (repo / "docs" / "artifact.md").read_text(encoding="utf-8") == "artifact"
    # The lock itself was still released on completion.
    assert not (repo / LOCK_NAME).exists()
