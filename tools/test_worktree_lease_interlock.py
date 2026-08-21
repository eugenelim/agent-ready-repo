"""Falsification tests for cleanup's cooperative exclusive lease."""

from __future__ import annotations

import inspect
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from tools.repo import coordination_lease
from tools.repo import worktree_hygiene as hygiene

PROCESS_START_BUDGET_SECONDS = 30
CLAIM_OBSERVATION_BUDGET_SECONDS = 30


class _Git:
    """Answer the narrowly scoped Git protocol the hygiene scanner uses."""

    def __init__(self, root: Path, common: Path) -> None:
        self.root = root
        self.common = common

    def __call__(
        self,
        argv: list[str],
        *,
        input: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del env
        if "worktree" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                f"worktree {self.root}\0HEAD abc\0branch refs/heads/test\0\0",
                "",
            )
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(argv, 0, f"{self.common}\n", "")
        if "check-ignore" in argv:
            return subprocess.CompletedProcess(argv, 0, input or "", "")
        if "ls-files" in argv:
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, "", "")


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    """Create one resolved worktree root and its Git common directory."""
    root = tmp_path.resolve()
    (root / ".git").mkdir()
    return root


def _candidate(root: Path, *, files: int = 1) -> Path:
    """Create a real ignored generated candidate with a controllable deletion cost."""
    build = root / "build"
    for index in range(files):
        leaf = build / f"part-{index // 50}" / f"artifact-{index}"
        leaf.parent.mkdir(parents=True, exist_ok=True)
        leaf.write_text("x", encoding="utf-8")
    return build


def _clean(root: Path, *, apply: bool, **kwargs: Any) -> tuple[int, list[str]]:
    """Invoke the real scanner and cleaner through its ordinary Git boundary."""
    return hygiene.clean(
        root,
        {"generated"},
        apply=apply,
        include_dependencies=False,
        protected=set(),
        runner=_Git(root, root / ".git"),
        **kwargs,
    )


def _delete_in_child(root_text: str, output: multiprocessing.Queue[Any]) -> None:
    """Run a real clean in a separate process so its held lock is observable."""
    root = Path(root_text)
    try:
        output.put(("result", _clean(root, apply=True)))
    except BaseException as error:
        output.put(("error", type(error).__name__, str(error)))


def test_clean_apply_refuses_a_live_activity_claim(worktree: Path) -> None:
    """A cleaner names the live holder and leaves its candidate untouched."""
    target = _candidate(worktree)
    claim = coordination_lease.acquire_activity(
        worktree / ".git", worktree, wait_seconds=0
    )
    try:
        code, lines = _clean(worktree, apply=True)
    finally:
        claim.release()

    receipt = "\n".join(lines)
    assert code == 75
    assert "WORKTREE_LEASE_DID_NOT_RUN" in lines
    assert f"pid {os.getpid()} in {worktree.name}" in receipt
    assert "clean did not run" in receipt
    assert target.exists()


def test_clean_apply_claim_spans_a_real_multi_file_deletion(worktree: Path) -> None:
    """The exclusive claim remains live while an actual candidate still exists."""
    target = _candidate(worktree, files=10_000)
    output: multiprocessing.Queue[Any] = multiprocessing.Queue()
    child = multiprocessing.Process(
        target=_delete_in_child,
        args=(str(worktree), output),
        daemon=True,
    )
    child.start()
    observed_claim = None
    observed_candidate = False
    deadline = time.monotonic() + CLAIM_OBSERVATION_BUDGET_SECONDS
    try:
        while time.monotonic() < deadline:
            claims = coordination_lease.read_claims(
                worktree / ".git", worktree, create=False
            )
            observed_claim = claims.exclusive
            observed_candidate = target.exists()
            if observed_claim is not None and observed_candidate:
                break
            if not child.is_alive():
                break
            time.sleep(0.01)
        child.join(PROCESS_START_BUDGET_SECONDS)
        assert observed_claim is not None and observed_candidate, (
            "expected an exclusive claim while the candidate existed; "
            f"observed_claim={observed_claim!r}, candidate_exists={observed_candidate}, "
            f"child_exitcode={child.exitcode}"
        )
        assert not target.exists()
        result = output.get(timeout=PROCESS_START_BUDGET_SECONDS)
        assert result[0] == "result", f"clean worker failed: {result!r}"
        code, lines = result[1]
        assert code == 0
        assert "lease: acquired exclusive claim" in lines
        assert "lease: released exclusive claim" in lines
        assert (
            coordination_lease.read_claims(
                worktree / ".git", worktree, create=False
            ).exclusive
            is None
        )
    finally:
        if child.is_alive():
            child.terminate()
        child.join(PROCESS_START_BUDGET_SECONDS)


def test_clean_dry_run_never_creates_a_claim_store(worktree: Path) -> None:
    """Preview remains lock-free and leaves no store behind."""
    target = _candidate(worktree)

    code, lines = _clean(worktree, apply=False)

    assert code == 0
    assert target.exists()
    assert not (worktree / ".git" / coordination_lease.LEASE_DIRECTORY).exists()
    assert not any(line.startswith("lease:") for line in lines)


def test_clean_offers_no_way_to_delete_without_a_lease(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No bypass may be reintroduced: deleting on absent evidence is a Never.

    Asserted on both surfaces, because removing only the flag would leave a
    parameter any in-repo caller could still pass.
    """
    with pytest.raises(SystemExit) as exit_result:
        hygiene.main(["clean", "--help"])

    assert exit_result.value.code == 0
    help_text = capsys.readouterr().out
    assert "--force-without-lease" not in help_text
    assert "without-lease" not in help_text
    assert "force_without_lease" not in inspect.signature(hygiene.clean).parameters


def test_clean_apply_refuses_an_unusable_store_with_no_override(
    worktree: Path,
) -> None:
    """A cleaner that cannot publish fails closed, and nothing reopens it."""
    target = _candidate(worktree)
    unusable_common = worktree / "not-a-directory"
    unusable_common.write_text("not a claim store", encoding="utf-8")

    code, lines = hygiene.clean(
        worktree,
        {"generated"},
        apply=True,
        include_dependencies=False,
        protected=set(),
        runner=_Git(worktree, unusable_common),
    )

    assert code == 75
    assert "WORKTREE_LEASE_DID_NOT_RUN" in lines
    assert "clean did not run" in "\n".join(lines)
    assert target.exists()
    # The refusal points at the recovery that does exist, rather than at a bypass.
    assert "release-claim" in "\n".join(lines)


def test_contended_roles_admit_exactly_one_participant(
    worktree: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The decision lock prevents both roles from proceeding or both refusing."""
    common = worktree / ".git"
    real_prune = coordination_lease._prune_not_live

    def slow_prune(paths: tuple[Path, ...], role: object, root: object) -> object:
        result = real_prune(paths, role, root)  # type: ignore[arg-type]
        time.sleep(0.25)
        return result

    monkeypatch.setattr(coordination_lease, "_prune_not_live", slow_prune)
    outcomes: dict[str, object] = {}
    start = threading.Barrier(2)

    def attempt(name: str, action: object) -> None:
        start.wait()
        try:
            outcomes[name] = action()  # type: ignore[operator]
        except coordination_lease.ClaimContentionError:
            outcomes[name] = None

    threads = [
        threading.Thread(
            target=attempt,
            args=(
                "activity",
                lambda: coordination_lease.acquire_activity(
                    common, worktree, wait_seconds=0
                ),
            ),
        ),
        threading.Thread(
            target=attempt,
            args=("exclusive", lambda: coordination_lease.acquire_exclusive(common, worktree)),
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(PROCESS_START_BUDGET_SECONDS)
    for claim in outcomes.values():
        if claim is not None:
            claim.release()  # type: ignore[union-attr]

    admitted = [name for name, claim in outcomes.items() if claim is not None]
    assert len(admitted) == 1, f"expected exactly one admitted role, observed {admitted}"


def test_activity_waits_for_an_exclusive_claim_to_clear(worktree: Path) -> None:
    """A build can wait out a deferrable cleanup instead of losing permanently."""
    common = worktree / ".git"
    exclusive = coordination_lease.acquire_exclusive(common, worktree)
    outcome: dict[str, object] = {}

    def acquire_activity() -> None:
        try:
            outcome["claim"] = coordination_lease.acquire_activity(
                common, worktree, wait_seconds=5
            )
        except BaseException as error:
            outcome["error"] = error

    waiter = threading.Thread(target=acquire_activity, daemon=True)
    released = False
    try:
        waiter.start()
        time.sleep(0.1)
        exclusive.release()
        released = True
        waiter.join(PROCESS_START_BUDGET_SECONDS)
        assert not waiter.is_alive(), "activity acquisition did not finish after release"
        assert "error" not in outcome, f"activity acquisition failed: {outcome!r}"
        claim = outcome.get("claim")
        assert claim is not None, f"activity acquisition produced no claim: {outcome!r}"
    finally:
        if not released:
            exclusive.release()
        claim = outcome.get("claim")
        if claim is not None:
            claim.release()  # type: ignore[union-attr]


@pytest.mark.skipif(sys.platform == "win32", reason="requires POSIX signals")
def test_clean_releases_the_claim_when_deletion_is_interrupted(worktree: Path) -> None:
    """An interrupt during real recursive deletion cannot strand an exclusive claim."""
    target = _candidate(worktree, files=10_000)
    first_leaf = target / "part-0" / "artifact-0"
    observed: dict[str, bool] = {"claim": False, "deletion": False}
    stop = threading.Event()

    def interrupt(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    def interrupt_after_deletion_starts() -> None:
        deadline = time.monotonic() + CLAIM_OBSERVATION_BUDGET_SECONDS
        while not stop.is_set() and time.monotonic() < deadline:
            claims = coordination_lease.read_claims(
                worktree / ".git", worktree, create=False
            )
            observed["claim"] = observed["claim"] or claims.exclusive is not None
            observed["deletion"] = observed["deletion"] or (
                observed["claim"] and not first_leaf.exists() and target.exists()
            )
            if observed["deletion"]:
                os.kill(os.getpid(), signal.SIGINT)
                return
            time.sleep(0.001)

    watcher = threading.Thread(target=interrupt_after_deletion_starts, daemon=True)
    previous_handler = signal.signal(signal.SIGINT, interrupt)
    try:
        watcher.start()
        with pytest.raises(KeyboardInterrupt):
            _clean(worktree, apply=True)
    finally:
        stop.set()
        watcher.join(PROCESS_START_BUDGET_SECONDS)
        signal.signal(signal.SIGINT, previous_handler)

    claims = coordination_lease.read_claims(worktree / ".git", worktree, create=False)
    assert observed["deletion"], f"interrupt never observed deletion: {observed}"
    assert claims.exclusive is None
