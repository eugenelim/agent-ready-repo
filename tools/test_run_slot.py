"""Construction tests for common-directory-wide heavy-run admission."""

from __future__ import annotations

import contextlib
import inspect
import json
import os
import threading
import time
import uuid
from pathlib import Path

import pytest

from tools.repo import coordination_lease

THREAD_BUDGET_SECONDS = 30.0


@pytest.fixture
def lease_root(tmp_path: Path) -> Path:
    """Provide one resolved common-directory fixture root per test case."""
    return tmp_path.resolve()


def _wait_for_ticket_count(root: Path, count: int) -> None:
    """Wait until real contenders have published the requested ticket count."""
    deadline = time.monotonic() + THREAD_BUDGET_SECONDS
    lease_dir = coordination_lease.prepare_lease_directory(root)
    while len(tuple(lease_dir.glob("run-ticket-*.lease"))) < count:
        assert time.monotonic() < deadline
        time.sleep(0.01)


def test_real_concurrent_admission_never_exceeds_limit(lease_root: Path) -> None:
    """A barrier makes five threads actually contend for two live slots."""
    environ = {
        coordination_lease.MAX_CONCURRENT_RUNS_ENV: "2",
        coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
    }
    active = 0
    maximum = 0
    guard = threading.Lock()
    failures: list[BaseException] = []
    start = threading.Barrier(5)

    def contender() -> None:
        nonlocal active, maximum
        try:
            start.wait(THREAD_BUDGET_SECONDS)
            claim = coordination_lease.acquire_run_slot(lease_root, environ=environ)
            with guard:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.1)
            with guard:
                active -= 1
            claim.release()
        except BaseException as error:
            failures.append(error)

    threads = [threading.Thread(target=contender) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(THREAD_BUDGET_SECONDS)
        assert not thread.is_alive()

    assert not failures
    assert maximum == 2


def test_ticket_removal_reregisters_without_losing_original_position(lease_root: Path) -> None:
    """Removing the first ticket cannot send that waiter behind a later waiter."""
    environ = {
        coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
        coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
    }
    holder = coordination_lease.acquire_run_slot(lease_root, environ=environ)
    admitted: list[str] = []
    failures: list[BaseException] = []

    def waiter(name: str) -> None:
        try:
            claim = coordination_lease.acquire_run_slot(lease_root, environ=environ)
            admitted.append(name)
            claim.release()
        except BaseException as error:
            failures.append(error)

    first = threading.Thread(target=waiter, args=("first",))
    first.start()
    _wait_for_ticket_count(lease_root, 1)
    lease_dir = coordination_lease.prepare_lease_directory(lease_root)
    first_ticket = next(iter(lease_dir.glob("run-ticket-*.lease")))

    second = threading.Thread(target=waiter, args=("second",))
    second.start()
    _wait_for_ticket_count(lease_root, 2)
    first_ticket.unlink()
    deadline = time.monotonic() + THREAD_BUDGET_SECONDS
    while not first_ticket.exists():
        assert time.monotonic() < deadline
        time.sleep(0.01)
    holder.release()
    for thread in (first, second):
        thread.join(THREAD_BUDGET_SECONDS)
        assert not thread.is_alive()

    assert not failures
    assert admitted == ["first", "second"]


def test_backdated_ticket_cannot_overtake_a_real_waiter(lease_root: Path) -> None:
    """A later ticket's forged payload time cannot put it at the queue front."""
    environ = {
        coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
        coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
    }
    holder = coordination_lease.acquire_run_slot(lease_root, environ=environ)
    admitted: list[coordination_lease.RunSlotClaim] = []
    failures: list[BaseException] = []

    def waiter() -> None:
        try:
            admitted.append(coordination_lease.acquire_run_slot(lease_root, environ=environ))
        except BaseException as error:
            failures.append(error)

    real_waiter = threading.Thread(target=waiter)
    real_waiter.start()
    _wait_for_ticket_count(lease_root, 1)
    lease_dir = coordination_lease.prepare_lease_directory(lease_root)
    forged_token = uuid.uuid4().hex
    forged_path = coordination_lease._run_claim_path(
        lease_dir, coordination_lease.ClaimRole.RUN_TICKET, forged_token
    )
    forged_payload = json.dumps(
        {
            "pid": os.getpid(),
            "worktree": str(lease_root),
            "created_at": 0,
            "token": forged_token,
        }
    )
    with coordination_lease.coordination_lock(lease_dir, "coordination.lock"):
        forged_descriptor = coordination_lease.publish_claim_candidate(
            lease_dir, forged_path, forged_payload
        )
    holder.release()
    real_waiter.join(THREAD_BUDGET_SECONDS)
    try:
        assert not real_waiter.is_alive()
        assert not failures
        assert len(admitted) == 1
    finally:
        if admitted:
            admitted[0].release()
        with contextlib.suppress(FileNotFoundError):
            forged_path.unlink()
        coordination_lease._unlock_and_close(forged_descriptor)


def test_admission_expiry_makes_limit_soft_but_worktree_claims_do_not_expire(
    lease_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aged slots are recoverable; safety interlocks retain their live holder."""
    environ = {
        coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
        coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
    }
    first = coordination_lease.acquire_run_slot(lease_root, environ=environ)
    observed_now = time.time()
    monkeypatch.setattr(
        coordination_lease.time,
        "time",
        lambda: observed_now + 7 * 60 * 60,
    )
    second = coordination_lease.acquire_run_slot(lease_root, environ=environ)
    activity = coordination_lease.acquire_activity(lease_root, lease_root, wait_seconds=1)
    monkeypatch.setattr(
        coordination_lease.time,
        "time",
        lambda: observed_now + 14 * 60 * 60,
    )

    try:
        retained = coordination_lease._prune_not_live(
            coordination_lease._claim_paths(
                activity.lease_dir, lease_root, coordination_lease.ClaimRole.ACTIVITY
            ),
            coordination_lease.ClaimRole.ACTIVITY,
            lease_root,
        )
        assert len(retained) == 1
    finally:
        second.release()
        first.release()
        activity.release()


def test_old_undeterminable_admission_record_expires(
    lease_root: Path,
) -> None:
    """A malformed admission record uses file age instead of resetting to now."""
    lease_dir = coordination_lease.prepare_lease_directory(lease_root)
    token = uuid.uuid4().hex
    path = coordination_lease._run_claim_path(
        lease_dir, coordination_lease.ClaimRole.RUN_SLOT, token
    )
    with coordination_lease.coordination_lock(lease_dir, "coordination.lock"):
        descriptor = coordination_lease.publish_claim_candidate(
            lease_dir,
            path,
            coordination_lease._run_claim_payload(token, lease_root),
        )
    os.ftruncate(descriptor, 0)
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.write(descriptor, b"{")
    old = time.time() - coordination_lease.RUN_CLAIM_MAX_AGE_SECONDS - 1
    os.utime(path, (old, old))
    try:
        records = coordination_lease._live_run_claims(
            lease_dir, coordination_lease.ClaimRole.RUN_SLOT, lease_root
        )
        assert records == ()
        assert not path.exists()
    finally:
        coordination_lease._unlock_and_close(descriptor)


def test_entrypoint_refuses_invalid_budget_before_store_access(
    lease_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed operator configuration cannot become an unleased run."""
    called = False

    def unexpected_store_access(common_dir: Path) -> Path:
        nonlocal called
        called = True
        return common_dir

    monkeypatch.setattr(coordination_lease, "prepare_lease_directory", unexpected_store_access)
    with pytest.raises(coordination_lease.RunSlotConfigurationError):
        coordination_lease.acquire_run_slot(
            lease_root,
            environ={coordination_lease.MAX_CONCURRENT_RUNS_ENV: "not-a-number"},
        )
    assert called is False


def test_entrypoint_preserves_store_unavailable_as_a_distinct_failure(
    lease_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Contention infrastructure failure is not mistaken for bad configuration."""
    def unavailable(common_dir: Path) -> Path:
        raise coordination_lease.ClaimStoreUnavailable("test store unavailable")

    monkeypatch.setattr(coordination_lease, "prepare_lease_directory", unavailable)
    with pytest.raises(coordination_lease.ClaimStoreUnavailable):
        coordination_lease.acquire_run_slot(
            lease_root,
            environ={
                coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
                coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
            },
        )


def test_budget_defaults_and_strict_parsing_are_literal_and_host_independent() -> None:
    """Defaults are contracted literals; malformed values never fall back."""
    source = inspect.getsource(coordination_lease)
    assert source.count("DEFAULT_MAX_CONCURRENT_RUNS = 2") == 1
    assert source.count("DEFAULT_RUN_SLOT_WAIT_SECONDS = 5400") == 1
    assert coordination_lease.memory_clamped_run_limit(2, None) == 2
    assert coordination_lease.run_slot_budgets({})[1] == 5400
    for invalid in ("0", "-1", " 1", "1.0", "many"):
        with pytest.raises(coordination_lease.RunSlotConfigurationError):
            coordination_lease.run_slot_budgets(
                {coordination_lease.MAX_CONCURRENT_RUNS_ENV: invalid}
            )
        with pytest.raises(coordination_lease.RunSlotConfigurationError):
            coordination_lease.run_slot_budgets(
                {coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: invalid}
            )


def test_memory_clamp_uses_twelve_gib_and_preserves_reference_headroom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default clamps down only, while explicit operator overrides remain."""
    gibibyte = 1024**3
    assert coordination_lease.memory_clamped_run_limit(2, 32 * gibibyte - 1) == 2
    assert coordination_lease.memory_clamped_run_limit(2, 16 * gibibyte) == 1
    assert coordination_lease.memory_clamped_run_limit(2, 128 * gibibyte) == 2
    monkeypatch.setattr(coordination_lease, "_physical_memory_bytes", lambda: 32 * gibibyte - 1)
    assert coordination_lease.run_slot_budgets({}) == (2, 5400)
    assert coordination_lease.run_slot_budgets(
        {coordination_lease.MAX_CONCURRENT_RUNS_ENV: "5"}
    )[0] == 5


def test_decision_lock_budget_scales_with_wait_budget_and_has_floor(
    lease_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Admission passes a proportional, minimum-30-second decision budget."""
    assert coordination_lease.run_slot_decision_lock_budget(1) == 30
    assert coordination_lease.run_slot_decision_lock_budget(5400) == 270
    observed: list[float | None] = []
    real_lock = coordination_lease.coordination_lock

    @contextlib.contextmanager
    def recording_lock(lease_dir: Path, name: str, **kwargs: object):
        observed.append(kwargs.get("acquisition_budget_seconds"))
        with real_lock(lease_dir, name, **kwargs):
            yield

    monkeypatch.setattr(coordination_lease, "coordination_lock", recording_lock)
    claim = coordination_lease.acquire_run_slot(
        lease_root,
        environ={
            coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
            coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "1000",
        },
    )
    try:
        assert observed
        assert all(budget == 50 for budget in observed)
    finally:
        monkeypatch.setattr(coordination_lease, "coordination_lock", real_lock)
        claim.release()


def test_scan_and_slot_publish_share_one_decision_lock_hold(
    lease_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Observe the lock around scan and publish instead of inferring it from a race."""
    events: list[str] = []
    real_lock = coordination_lease.coordination_lock
    real_claims = coordination_lease._live_run_claims
    real_publish = coordination_lease.publish_claim_candidate

    @contextlib.contextmanager
    def recording_lock(lease_dir: Path, name: str, **kwargs: object):
        events.append("enter")
        with real_lock(lease_dir, name, **kwargs):
            yield
        events.append("exit")

    def recording_claims(lease_dir: Path, role: coordination_lease.ClaimRole, common_dir: Path):
        if role is coordination_lease.ClaimRole.RUN_SLOT:
            events.append("scan")
        return real_claims(lease_dir, role, common_dir)

    def recording_publish(lease_dir: Path, path: Path, payload: str) -> int:
        if path.name.startswith("run-slot-"):
            events.append("publish")
        return real_publish(lease_dir, path, payload)

    monkeypatch.setattr(coordination_lease, "coordination_lock", recording_lock)
    monkeypatch.setattr(coordination_lease, "_live_run_claims", recording_claims)
    monkeypatch.setattr(coordination_lease, "publish_claim_candidate", recording_publish)
    claim = coordination_lease.acquire_run_slot(
        lease_root,
        environ={
            coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
            coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
        },
    )
    claim.release()

    scan = events.index("scan")
    publish = events.index("publish")
    enter = max(index for index, event in enumerate(events[:scan]) if event == "enter")
    exit_index = next(index for index, event in enumerate(events[scan:], scan) if event == "exit")
    assert enter < scan < publish < exit_index


def test_release_is_idempotent(lease_root: Path) -> None:
    """A second release cannot close a file descriptor recycled by another caller."""
    claim = coordination_lease.acquire_run_slot(
        lease_root,
        environ={
            coordination_lease.MAX_CONCURRENT_RUNS_ENV: "1",
            coordination_lease.RUN_SLOT_WAIT_SECONDS_ENV: "30",
        },
    )
    claim.release()
    claim.release()
    assert claim.descriptor is None
