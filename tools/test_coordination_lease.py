"""Construction tests for cooperative worktree coordination claims."""

from __future__ import annotations

import inspect
import json
import multiprocessing
import os
import signal
import threading
import time
from pathlib import Path

import pytest

from tools.repo import coordination_lease

# Waiting for a real child process to start is the one cost here that genuinely
# scales with machine load, and this host has run at load 47-160 with swap
# exhausted. A 2-second budget produced a baseline failure that looked exactly
# like a logic defect -- the same trap AC14 addresses for the vitest case. Widen
# the budget for the thing whose cost varies; keep every assertion tight. One
# home, so it cannot drift between call sites.
CHILD_START_BUDGET_SECONDS = 60.0


@pytest.fixture
def claim_holder_processes() -> list[multiprocessing.Process]:
    """Track daemon claim holders so a failed assertion cannot hang pytest."""
    holders: list[multiprocessing.Process] = []
    yield holders
    for holder in holders:
        if holder.is_alive():
            holder.terminate()
        holder.join(CHILD_START_BUDGET_SECONDS)


def _start_claim_holder(
    holders: list[multiprocessing.Process], root: Path, worktree: Path
) -> tuple[multiprocessing.Process, multiprocessing.synchronize.Event]:
    """Start one daemon holder and return it with its readiness event."""
    ready = multiprocessing.Event()
    holder = multiprocessing.Process(
        target=_claim_holder,
        args=(str(root), str(worktree), ready),
        daemon=True,
    )
    holders.append(holder)
    holder.start()
    return holder, ready


def _lock_worker(directory: str, ready: multiprocessing.synchronize.Event, queue: multiprocessing.queues.Queue[float]) -> None:
    """Hold the real cross-process lock until the parent measures it."""
    with coordination_lease.coordination_lock(Path(directory), "real-process.lock"):
        ready.set()
        started = time.monotonic()
        time.sleep(0.2)
    queue.put(time.monotonic() - started)


def _claim_holder(common_dir: str, worktree: str, ready: multiprocessing.synchronize.Event) -> None:
    """Acquire a real claim and remain alive until the parent kills this process."""
    claim = coordination_lease.acquire_exclusive(Path(common_dir), Path(worktree))
    ready.set()
    while True:
        assert claim.path.exists()
        time.sleep(1)


def test_atomic_publish_second_publisher_never_overwrites(tmp_path: Path) -> None:
    """A hard-link publication leaves the first complete payload intact."""
    root = tmp_path.resolve()
    lease_dir = coordination_lease.prepare_lease_directory(root)
    path = lease_dir / "claim.lease"

    coordination_lease.publish_claim_candidate(lease_dir, path, "first")
    with pytest.raises(FileExistsError):
        coordination_lease.publish_claim_candidate(lease_dir, path, "second")

    assert path.read_text(encoding="utf-8") == "first"


def test_release_removes_only_callers_own_claim(tmp_path: Path) -> None:
    """A stale handle cannot unlink a peer that replaced its file."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    claim = coordination_lease.acquire_exclusive(root, worktree)
    replacement = {**json.loads(claim.path.read_text()), "token": "replacement"}
    claim.path.write_text(json.dumps(replacement), encoding="utf-8")

    claim.release()

    assert claim.path.exists()


def test_sigkilled_holder_claim_is_reclaimed(
    tmp_path: Path, claim_holder_processes: list[multiprocessing.Process]
) -> None:
    """The kernel releases a real killed holder's claim lock for reclamation."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    holder, ready = _start_claim_holder(claim_holder_processes, root, worktree)
    assert ready.wait(CHILD_START_BUDGET_SECONDS)
    os.kill(holder.pid, signal.SIGKILL)
    holder.join(CHILD_START_BUDGET_SECONDS)

    second = coordination_lease.acquire_exclusive(root, worktree)

    assert second.path.exists()
    second.release()


def test_live_identity_is_not_reclaimed_by_age_alone(
    tmp_path: Path, claim_holder_processes: list[multiprocessing.Process]
) -> None:
    """A live lifetime lock is protected even when metadata says it is old."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    holder, ready = _start_claim_holder(claim_holder_processes, root, worktree)
    assert ready.wait(CHILD_START_BUDGET_SECONDS)
    path = coordination_lease.read_claims(root, worktree).exclusive.path
    payload = json.loads(path.read_text())
    payload["created_at"] = 0
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(coordination_lease.ClaimContentionError):
        coordination_lease.acquire_exclusive(root, worktree)
    os.kill(holder.pid, signal.SIGKILL)
    holder.join(CHILD_START_BUDGET_SECONDS)


def test_unreadable_payload_is_undeterminable_and_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Garbage is not evidence that it is safe to take a claim."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    first = coordination_lease.acquire_exclusive(root, worktree)
    first.path.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(coordination_lease, "_probe_claim_lock", lambda _path: coordination_lease.Liveness.UNDETERMINABLE)

    claims = coordination_lease.read_claims(root, worktree)

    assert claims.exclusive is not None
    assert claims.exclusive.liveness is coordination_lease.Liveness.UNDETERMINABLE
    with pytest.raises(coordination_lease.ClaimContentionError):
        coordination_lease.acquire_exclusive(root, worktree)


@pytest.mark.parametrize("mutation", ["out_of_range", "wrong_worktree", "future"])
def test_untrusted_payloads_are_rejected(tmp_path: Path, mutation: str) -> None:
    """Malformed identity, location, and time data cannot be trusted."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    claim = coordination_lease.acquire_exclusive(root, worktree)
    payload = json.loads(claim.path.read_text())
    if mutation == "out_of_range":
        payload["pid"] = -1
    elif mutation == "wrong_worktree":
        payload["worktree"] = "/mnt/other-worktree"
    else:
        payload["created_at"] = time.time() + 3600
    claim.path.write_text(json.dumps(payload), encoding="utf-8")

    read = coordination_lease.read_claims(root, worktree).exclusive

    assert read is not None
    assert read.pid is None if mutation != "future" else read.pid == os.getpid()
    if mutation == "future":
        assert read.created_at <= time.time()


def test_recycled_pid_cannot_impersonate_lock_holder(
    tmp_path: Path, claim_holder_processes: list[multiprocessing.Process]
) -> None:
    """Payload PIDs are only diagnostics; the held descriptor establishes liveness."""
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    holder, ready = _start_claim_holder(claim_holder_processes, root, worktree)
    assert ready.wait(CHILD_START_BUDGET_SECONDS)
    path = coordination_lease.read_claims(root, worktree).exclusive.path
    payload = json.loads(path.read_text())
    payload["pid"] = 999_999_999
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert coordination_lease.read_claims(root, worktree).exclusive.liveness is coordination_lease.Liveness.LIVE
    os.kill(holder.pid, signal.SIGKILL)
    holder.join(CHILD_START_BUDGET_SECONDS)


def test_a_forged_claim_with_a_live_pid_is_not_live(tmp_path: Path) -> None:
    """A hand-written claim naming a definitely-live pid is NOT live.

    This is the direction the recycled-pid test cannot cover. That test corrupts
    a payload while a real holder holds the lock and asserts LIVE -- which stays
    true if liveness were hardcoded to LIVE, so it cannot detect a
    payload-derived implementation. This case asserts the opposite: a claim file
    with no lock holder is NOT_LIVE even though its recorded pid is this very
    process and so unambiguously alive.

    It is also the security case directly: a forged claim naming pid 1, or any
    live pid, must not be able to wedge the tool permanently. The lock decides,
    and nothing forged can hold one.
    """
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    lease_dir = coordination_lease.prepare_lease_directory(root)
    key = coordination_lease.worktree_key(worktree)
    forged = lease_dir / f"exclusive-{key}.lease"
    forged.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "worktree": str(worktree),
                "created_at": time.time(),
                "token": "forged",
            }
        ),
        encoding="utf-8",
    )

    record = coordination_lease.read_claims(root, worktree).exclusive
    assert record is not None
    assert record.pid == os.getpid()
    assert record.liveness is coordination_lease.Liveness.NOT_LIVE

    # And therefore it cannot block a real acquisition.
    claim = coordination_lease.acquire_exclusive(root, worktree)
    claim.release()


def test_digest_keys_do_not_flatten_distinct_worktree_paths(tmp_path: Path) -> None:
    """Separators never collapse into a filename identity."""
    root = tmp_path.resolve()

    assert coordination_lease.worktree_key(Path("/mnt/a/b-c")) != coordination_lease.worktree_key(Path("/mnt/a-b/c"))
    assert len(coordination_lease.worktree_key(root)) == 64


def test_symlinked_lease_directory_is_refused(tmp_path: Path) -> None:
    """mkdir's symlink-following behaviour cannot bless a redirected store."""
    root = tmp_path.resolve()
    outside = (root / "outside").resolve()
    outside.mkdir()
    (root / coordination_lease.LEASE_DIRECTORY).symlink_to(outside, target_is_directory=True)

    with pytest.raises(coordination_lease.ClaimStoreUnavailable):
        coordination_lease.prepare_lease_directory(root)


def test_claim_path_escaping_lease_directory_is_refused(tmp_path: Path) -> None:
    """Publication only accepts a claim path confined to the prepared store."""
    root = tmp_path.resolve()
    lease_dir = coordination_lease.prepare_lease_directory(root)

    with pytest.raises(coordination_lease.ClaimStoreUnavailable):
        coordination_lease.publish_claim_candidate(lease_dir, root / "escape.lease", "payload")


def test_claim_directory_symlink_is_refused(tmp_path: Path) -> None:
    """Publisher lstat-checks its own directory, not only its child path."""
    root = tmp_path.resolve()
    target = (root / "target").resolve()
    target.mkdir()
    linked_directory = root / "linked-lease-directory"
    linked_directory.symlink_to(target, target_is_directory=True)

    with pytest.raises(coordination_lease.ClaimStoreUnavailable):
        coordination_lease.publish_claim_candidate(
            linked_directory, linked_directory / "claim.lease", "payload"
        )


def test_claim_lock_operations_seek_to_byte_zero_structurally() -> None:
    """Windows byte-range liveness needs both operations to overlap byte zero."""
    publish_source = inspect.getsource(coordination_lease.publish_claim_candidate)
    probe_source = inspect.getsource(coordination_lease._probe_claim_lock)
    release_source = inspect.getsource(coordination_lease._unlock_and_close)

    assert publish_source.index("os.lseek(descriptor, 0, os.SEEK_SET)") < publish_source.index(
        "_lock_functions(descriptor)[0]()"
    )
    assert probe_source.index("os.lseek(descriptor, 0, os.SEEK_SET)") < probe_source.index(
        "acquire()"
    )
    assert probe_source.count("os.lseek(descriptor, 0, os.SEEK_SET)") >= 2
    assert release_source.index("os.lseek(descriptor, 0, os.SEEK_SET)") < release_source.index(
        "_lock_functions(descriptor)[1]()"
    )


def test_coordination_lock_serializes_two_real_processes(tmp_path: Path) -> None:
    """The filesystem lock, rather than a mock, excludes another process."""
    root = tmp_path.resolve()
    coordination_lease.prepare_lease_directory(root)
    ready = multiprocessing.Event()
    queue: multiprocessing.Queue[float] = multiprocessing.Queue()
    child = multiprocessing.Process(target=_lock_worker, args=(str(root / coordination_lease.LEASE_DIRECTORY), ready, queue))
    child.start()
    assert ready.wait(CHILD_START_BUDGET_SECONDS)
    started = time.monotonic()
    with coordination_lease.coordination_lock(root / coordination_lease.LEASE_DIRECTORY, "real-process.lock"):
        waited = time.monotonic() - started
    child.join(CHILD_START_BUDGET_SECONDS)

    assert child.exitcode == 0
    assert waited >= 0.15


def test_racing_participants_are_never_both_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC6's central claim: read-other-role and publish-own are indivisible.

    A slow read makes the window observable. Without the shared decision lock,
    each participant reads before the other has published and BOTH are admitted
    -- which is exactly the check-to-delete race the lease exists to close. With
    it, one of them must lose.

    Threads rather than processes, because the decision lock is `flock` on a
    freshly opened descriptor per call, so two threads contend for it just as two
    processes do -- and a thread can be given the patched slow read that widens
    the window deterministically, instead of hoping a race reproduces.
    """
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()

    real_prune = coordination_lease._prune_not_live

    def slow_prune(paths: tuple[Path, ...], role: object, wt: object) -> object:
        result = real_prune(paths, role, wt)  # type: ignore[arg-type]
        time.sleep(0.25)
        return result

    monkeypatch.setattr(coordination_lease, "_prune_not_live", slow_prune)

    outcomes: dict[str, object] = {}

    def attempt(name: str, action: object) -> None:
        try:
            outcomes[name] = action()  # type: ignore[operator]
        except (
            coordination_lease.ClaimContentionError,
            coordination_lease.ClaimStoreUnavailable,
        ):
            outcomes[name] = None

    threads = [
        threading.Thread(
            target=attempt,
            args=(
                "activity",
                lambda: coordination_lease.acquire_activity(
                    root, worktree, wait_seconds=0
                ),
            ),
        ),
        threading.Thread(
            target=attempt,
            args=("exclusive", lambda: coordination_lease.acquire_exclusive(root, worktree)),
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(15)
        assert not thread.is_alive()

    admitted = sorted(name for name, claim in outcomes.items() if claim is not None)
    for claim in outcomes.values():
        if claim is not None:
            claim.release()  # type: ignore[union-attr]

    assert len(admitted) <= 1, f"both roles admitted at once: {admitted}"


def test_sequential_interlock_refuses_exclusive_while_activity_is_held(
    tmp_path: Path,
) -> None:
    """The interlock in the sequential case. NOT an atomicity proof.

    This was originally named for interleaving, but it interleaves nothing: it
    acquires, then asserts the other role refuses. It passes with the decision
    lock removed entirely, so it cannot testify about AC6's indivisibility
    requirement. The real proof is the racing test below; this one is retained
    because the sequential refusal is worth pinning on its own.
    """
    root = tmp_path.resolve()
    worktree = (root / "worktree").resolve()
    worktree.mkdir()
    observed = coordination_lease.read_claims(root, worktree)
    assert observed.exclusive is None

    first = coordination_lease.acquire_activity(root, worktree, wait_seconds=0)
    with pytest.raises(coordination_lease.ClaimContentionError):
        coordination_lease.acquire_exclusive(root, worktree)
    first.release()
