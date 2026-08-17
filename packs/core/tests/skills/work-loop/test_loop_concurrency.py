#!/usr/bin/env python3
"""Pytest concurrency regressions for loop-cohort.py and loop-engine.py.

Run with pytest.

These are the acceptance bar for docs/specs/loop-cohort-state-lock. Both cases
were observed failing against the pre-fix tree — see notes/reproduction.md.

THE HARNESS IS THE POINT. The synchronising barrier sits AFTER interpreter and
module startup. Child 0 then holds the production state lock until every
follower proves it contended on that lock. Without an explicit contention
handshake, process startup and scheduler fairness can smear the children apart,
letting a naive fan-out pass against the unfixed tree.

Separate OS processes, never threads: threads share os.chdir, the module-level
_lint_module global, and sys.stdout, so they neither exercise the cross-process
contract the lock exists for nor permit sound per-caller exit-code assertions.

Hermetic: every case runs against a throwaway git repo so loop-engine's
_get_repo_root() resolves inside tmp_path. Every child records that resolved
root, so the suite verifies its own boundary without treating unrelated writes
to the live checkout as test failures.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spawn_support as ss  # noqa: E402 — sibling support module, path set above

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"
if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
COHORT = SCRIPT_DIR / "loop-cohort.py"
ENGINE = SCRIPT_DIR / "loop-engine.py"

# Ceiling on the parent's wait for every child to finish loading its module.
# Not a per-trial cost: the wait normally ends in tens of ms.
READY_TIMEOUT = 30.0
# Parent-side ceiling, not a pass/fail timing assertion. A child already gives
# each synchronization wait READY_TIMEOUT; twice that budget leaves one full
# interval for process teardown and a subject command while preventing an outer
# CI job timeout from becoming the only diagnostic.
HARNESS_PROCESS_TIMEOUT = READY_TIMEOUT * 2

# The barriered child, in two phases. A *guessed* lead is what smears children
# apart on a loaded runner — measured at 495 ms and 3756 ms of spread with a 1 s
# lead, which silently destroys the suite's discriminating power. The old
# replacement still inferred overlap from a 50 ms post-release arrival spread;
# scheduler fairness made that assertion flaky, and even a tight spread did not
# prove the microsecond-wide critical sections overlapped.
#
# This child proves the relevant event directly. Child 0 acquires the real
# production state lock and holds it until every follower has timed out once
# against that occupied lock. Only then may the leader mutate and release; each
# follower retries normally afterward. Slow scheduling changes how long the
# handshake takes, never whether the case passes.
_CHILD_SRC = '''
import contextlib, importlib.util, os, sys, time
from pathlib import Path
ready_file = Path(sys.argv[1]); go_file = Path(sys.argv[2])
probe_dir = Path(sys.argv[3]); repo_root_file = Path(sys.argv[4])
child_index = int(sys.argv[5]); child_count = int(sys.argv[6])
sync_timeout = float(sys.argv[7]); target = sys.argv[8]; argv = sys.argv[9:]

def wait_for(predicate, description):
    deadline = time.monotonic() + sync_timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise RuntimeError(f"sync timeout waiting for {description}")
        time.sleep(0.005)

spec = importlib.util.spec_from_file_location("_subject", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)          # startup paid BEFORE announcing ready

resolved_root = mod._get_repo_root() if hasattr(mod, "_get_repo_root") else Path.cwd()
repo_root_file.write_text(str(resolved_root), encoding="utf-8")
real_statelock = mod._statelock()
disable_lock = os.environ.get("LOOP_CONCURRENCY_TEST_DISABLE_LOCK") == "1"

if disable_lock:
    write_name = (
        "_write_engine_state_atomic"
        if hasattr(mod, "_write_engine_state_atomic")
        else "write_state_atomic"
    )
    real_write = getattr(mod, write_name)

    def synchronized_unlocked_write(*args, **kwargs):
        (probe_dir / f"unlocked-write-{child_index}").write_text("1", encoding="ascii")
        wait_for(
            lambda: len(list(probe_dir.glob("unlocked-write-*"))) == child_count,
            f"{child_count} unlocked writers to reach the state-write boundary",
        )
        return real_write(*args, **kwargs)

    setattr(mod, write_name, synchronized_unlocked_write)

class ProbedStateLock:
    def __getattr__(self, name):
        return getattr(real_statelock, name)

    @contextlib.contextmanager
    def exclusive(self, path):
        if disable_lock:
            yield real_statelock.lock_path_for(path)
            return

        leader_held = probe_dir / "leader-held"
        leader_released = probe_dir / "leader-released"
        if child_index == 0:
            try:
                with real_statelock.exclusive(path) as lock:
                    leader_held.write_text("1", encoding="ascii")
                    wait_for(
                        lambda: len(list(probe_dir.glob("contended-*")))
                        == child_count - 1,
                        f"{child_count - 1} followers to contend",
                    )
                    yield lock
            finally:
                leader_released.write_text("1", encoding="ascii")
            return

        wait_for(leader_held.exists, "leader to hold the state lock")
        try:
            with real_statelock.exclusive(path, timeout=0.1, poll=0.005):
                raise RuntimeError("follower acquired while leader still held the lock")
        except real_statelock.StateLockTimeout:
            (probe_dir / f"contended-{child_index}").write_text("1", encoding="ascii")
        wait_for(leader_released.exists, "leader to release the state lock")
        with real_statelock.exclusive(path) as lock:
            yield lock

mod._statelock = lambda: ProbedStateLock()
ready_file.write_text("1", encoding="ascii")  # phase 1: announce
wait_for(go_file.exists, "parent go signal")  # phase 2: rendezvous
sys.exit(mod.main(argv))
'''

_last_sync: dict[str, str] = {}


def ok(name: str) -> None:
    """Pytest reports the independently collected case."""


def fail(name: str, reason: str) -> None:
    sync = _last_sync.get(name, "not applicable")
    pytest.fail(f"{name}: {reason} (sync: {sync})")


# ── hermetic fixture helpers (shape borrowed from
#    test_loop_engine_events_jsonl.py so _get_repo_root() lands in tmp_path) ──

def _child_path(root: Path) -> Path:
    p = root / "_barriered_child.py"
    if not p.exists():
        p.write_text(_CHILD_SRC, encoding="utf-8")
    return p


def _init_git_repo(path: Path) -> Path:
    subprocess.run(
        ["git", "init", str(path)],
        check=True,
        capture_output=True,
        timeout=HARNESS_PROCESS_TIMEOUT,
    )
    for cmd in (["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"]):
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            cwd=str(path),
            timeout=HARNESS_PROCESS_TIMEOUT,
        )
    return path


def _make_spec_dir(repo: Path, name: str) -> Path:
    spec_dir = repo / "docs" / "specs" / name
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text("- **Status:** Approved\n")
    (spec_dir / "plan.md").write_text("- **Status:** Approved\n")
    return spec_dir


def _run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=str(cwd), timeout=HARNESS_PROCESS_TIMEOUT)


def _engine_init(repo: Path, spec_dir: Path) -> str:
    r = _run(ENGINE, "init", str(spec_dir), "--mode", "code", "--json", cwd=repo)
    assert r.returncode == 0, r.stderr
    run_id = json.loads(r.stdout.strip())["run_id"]
    r = _run(COHORT, "init", str(spec_dir), "--run-id", run_id, cwd=repo)
    assert r.returncode == 0, r.stderr
    return run_id


def _load_module(path: Path, name: str):
    """Load a module by path so the test can read its constants."""
    import importlib.util as _il
    spec = _il.spec_from_file_location(name, str(path))
    mod = _il.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_barriered(n: int, target: Path, argvs: list[list[str]], cwd: Path):
    """Launch n children through a proven real-lock contention handshake.

    argvs is one argv per child. Returns per-child results plus readiness,
    contention, and resolved-repository evidence.
    """
    child = _child_path(cwd)
    probe_dir = cwd / "_probe"
    probe_dir.mkdir(exist_ok=True)
    for stale in probe_dir.iterdir():
        stale.unlink()

    roots_dir = cwd / "_roots"
    roots_dir.mkdir(exist_ok=True)
    for stale in roots_dir.iterdir():
        stale.unlink()

    ready_dir = cwd / "_ready"
    ready_dir.mkdir(exist_ok=True)
    for stale in ready_dir.iterdir():
        stale.unlink()
    go_file = cwd / "_go"
    go_file.unlink(missing_ok=True)

    procs = [
        subprocess.Popen(
            [sys.executable, str(child), str(ready_dir / f"{i}.txt"),
             str(go_file), str(probe_dir), str(roots_dir / f"{i}.txt"),
             str(i), str(n), str(READY_TIMEOUT), str(target), *argvs[i]],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", cwd=str(cwd),
        )
        for i in range(n)
    ]
    # Phase 1: wait for every child to finish interpreter + module startup.
    deadline = time.monotonic() + READY_TIMEOUT
    while len(list(ready_dir.iterdir())) < n and time.monotonic() < deadline:
        time.sleep(0.005)
    ready = len(list(ready_dir.iterdir()))
    # Phase 2: release them all at once.
    go_file.write_text("go")

    outputs: list[tuple[str, str] | None] = [None] * n
    timed_out: list[int] = []
    process_deadline = time.monotonic() + HARNESS_PROCESS_TIMEOUT
    for i, proc in enumerate(procs):
        remaining = max(0.0, process_deadline - time.monotonic())
        try:
            outputs[i] = proc.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = [
                j for j, child_proc in enumerate(procs)
                if outputs[j] is None and child_proc.poll() is None
            ]
            for j in timed_out:
                procs[j].kill()
            for j, child_proc in enumerate(procs):
                if outputs[j] is None:
                    outputs[j] = child_proc.communicate()
            break
    results = [
        (proc.returncode, *(outputs[i] or ("", "")))
        for i, proc in enumerate(procs)
    ]

    roots = []
    for f in sorted(roots_dir.iterdir()):
        with contextlib.suppress(OSError):
            roots.append(f.read_text(encoding="utf-8").strip())
    contended = len(list(probe_dir.glob("contended-*")))
    unlocked_writes = len(list(probe_dir.glob("unlocked-write-*")))
    return results, ready, contended, unlocked_writes, roots, timed_out


# STUB: AC20
def _check_contention(
    name: str,
    n: int,
    ready: int,
    contended: int,
    unlocked_writes: int,
    roots: list[str],
    timed_out: list[int],
    cwd: Path,
) -> bool:
    """Verify real contention, or synchronized stale writes in proof mode."""
    expected_root = str(cwd.resolve())
    root_mismatches = [root for root in roots if root != expected_root]
    observed = (
        f"ready={ready}/{n}, contended={contended}/{n - 1}, "
        f"unlocked_writes={unlocked_writes}/{n}, repo_roots={len(roots)}/{n}, "
        f"timed_out={timed_out}"
    )
    _last_sync[name] = observed
    expected_probe = (
        unlocked_writes == n
        if os.environ.get("LOOP_CONCURRENCY_TEST_DISABLE_LOCK") == "1"
        else contended == n - 1 and unlocked_writes == 0
    )
    if (
        ready != n
        or timed_out
        or not expected_probe
        or len(roots) != n
        or root_mismatches
    ):
        detail = f"; mismatched roots={root_mismatches!r}" if root_mismatches else ""
        fail(
            name,
            f"race handshake incomplete{detail} — a pass would not prove the "
            "state lock serialized these calls",
        )
        return False
    return True


# ── AC15 — cohort: no lost update ──────────────────────────────────────────

# STUB: AC17
def test_concurrent_record_attempt_no_lost_update(tmp: Path) -> None:
    """Pre-fix: 20/20 trials lost an update at N=2 (notes/reproduction.md A)."""
    for n, trials in ((2, 6), (8, 3)):
        for trial in range(trials):
            root = tmp / f"rec-{n}-{trial}"
            root.mkdir(parents=True)
            repo = _init_git_repo(root)
            spec_dir = _make_spec_dir(repo, "demo")
            run_id = _engine_init(repo, spec_dir)
            argvs = [
                ["record-attempt", str(spec_dir), "--phase", "implement",
                 "--cycle-id", f"{run_id}:{i}", "--expect-run-id", run_id]
                for i in range(n)
            ]
            res, ready, contended, unlocked_writes, roots, timed_out = _run_barriered(
                n, COHORT, argvs, repo
            )
            if not _check_contention(
                "record-attempt-no-lost-update",
                n,
                ready,
                contended,
                unlocked_writes,
                roots,
                timed_out,
                repo,
            ):
                return
            succeeded = sum(1 for rc, _, _ in res if rc == 0)
            got = json.loads((spec_dir / "state.json").read_text(
                encoding="utf-8"))["implementation_retry_count"]
            # Assert against N, not against `succeeded`. Comparing to
            # `succeeded` lets a too-eager implementation pass: if N-1
            # contenders hit StateLockTimeout and refuse, succeeded == got == 1
            # and the headline regression goes green on a broken lock.
            if succeeded != n or got != n:
                detail = " | ".join(
                    f"rc={rc} {(so + se).strip()[:120]!r}" for rc, so, se in res
                )
                fail("record-attempt-no-lost-update",
                     f"N={n} trial={trial}: {succeeded}/{n} calls exited 0 and "
                     f"implementation_retry_count={got}; both must equal {n}. {detail}")
                return
    ok("record-attempt-no-lost-update")


# ── AC16 — engine: exactly one transition admitted, one audit record ───────

# STUB: AC18
def test_concurrent_identical_transition(tmp: Path) -> None:
    """Pre-fix: 10/10 trials admitted BOTH (notes/reproduction.md B)."""
    for trial in range(4):
        root = tmp / f"tr-{trial}"
        root.mkdir(parents=True)
        repo = _init_git_repo(root)
        spec_dir = _make_spec_dir(repo, "demo")
        _engine_init(repo, spec_dir)
        argvs = [["transition", str(spec_dir), "spec-ready"] for _ in range(2)]
        res, ready, contended, unlocked_writes, roots, timed_out = _run_barriered(
            2, ENGINE, argvs, repo
        )
        if not _check_contention(
            "concurrent-identical-transition",
            2,
            ready,
            contended,
            unlocked_writes,
            roots,
            timed_out,
            repo,
        ):
            return

        winners = [r for r in res if r[0] == 0]
        losers = [r for r in res if r[0] != 0]
        if len(winners) != 1:
            fail("concurrent-identical-transition",
                 f"trial={trial}: {len(winners)} transitions exited 0, expected 1")
            return
        blob = (losers[0][1] + losers[0][2]) if losers else ""
        if "illegal transition" not in blob:
            fail("concurrent-identical-transition",
                 f"trial={trial}: loser did not refuse with 'illegal transition' "
                 f"(a lock timeout does not satisfy AC16): {blob.strip()!r}")
            return

        state = json.loads((spec_dir / "engine-state.json").read_text(
            encoding="utf-8"))
        if state["transition_sequence"] != 1:
            fail("concurrent-identical-transition",
                 f"trial={trial}: transition_sequence={state['transition_sequence']}, "
                 "expected 1")
            return

        events_path = repo / ".loop-run" / "events.jsonl"
        rows = [json.loads(line) for line in
                events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        keys = [(r.get("spec"), r.get("seq")) for r in rows]
        if len(keys) != len(set(keys)):
            fail("concurrent-identical-transition",
                 f"trial={trial}: duplicate (spec, seq) in the audit outbox: {keys}")
            return
    ok("concurrent-identical-transition")


# ── AC17 — init is not racy ────────────────────────────────────────────────

# STUB: AC19
def test_concurrent_init(tmp: Path) -> None:
    n = 6
    root = tmp / "init"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    run_id = "20260807T000000Z-init"
    argvs = [["init", str(spec_dir), "--run-id", run_id] for _ in range(n)]
    res, ready, contended, unlocked_writes, roots, timed_out = _run_barriered(
        n, COHORT, argvs, repo
    )
    if not _check_contention(
        "concurrent-init",
        n,
        ready,
        contended,
        unlocked_writes,
        roots,
        timed_out,
        repo,
    ):
        return
    winners = [r for r in res if r[0] == 0]
    losers = [r for r in res if r[0] != 0]
    if len(winners) != 1:
        fail("concurrent-init",
             f"{len(winners)} init calls exited 0, expected exactly 1")
        return
    # The loser must refuse for the RIGHT reason: N-1 lock timeouts would
    # satisfy a bare winners==1 check while proving nothing about the race.
    for rc, so, se in losers:
        if "already exists" not in (so + se):
            fail("concurrent-init",
                 f"a loser refused for the wrong reason (rc={rc}): {(so + se).strip()!r}")
            return
    ok("concurrent-init")


# ── AC15 — every locked verb refuses when the lock is held, writing nothing ──

def _plant_unacquirable(state_file: Path) -> Path:
    """Make the lock path unacquirable, refused immediately.

    A directory at the lock path is refused at once (StateLockUnusable) rather
    than waited out, so the nine-verb sweep costs milliseconds instead of nine
    full timeouts — ~90 s. AC15 covers "cannot be acquired for ANY reason", and
    the contended path gets its own case below.
    """
    lock = state_file.with_name(state_file.name + ".lock")
    lock.mkdir()
    return lock


def _plant_contended(state_file: Path) -> Path:
    """A fresh, well-formed lockfile: held by someone else, so it is waited out."""
    lock = state_file.with_name(state_file.name + ".lock")
    lock.write_text("statelock1 " + "e" * 32 + " 1234567\n", encoding="utf-8")
    return lock


# STUB: AC15
def test_locked_verbs_refuse_when_held(tmp: Path) -> None:
    """The WIRING, not the module: a module-level timeout test proves nothing
    about whether each verb was actually wrapped. All TEN locked verbs."""
    root = tmp / "refuse"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    run_id = _engine_init(repo, spec_dir)

    cohort_state = spec_dir / "state.json"
    engine_state = spec_dir / "engine-state.json"

    cases = [
        (COHORT, cohort_state, "approve-plan",
         ["approve-plan", str(spec_dir), "--expect-run-id", run_id]),
        (COHORT, cohort_state, "schedule",
         ["schedule", str(spec_dir), "--expect-run-id", run_id]),
        (COHORT, cohort_state, "wave advance",
         ["wave", "advance", str(spec_dir), "--from-index", "0",
          "--expect-run-id", run_id]),
        (COHORT, cohort_state, "record-attempt",
         ["record-attempt", str(spec_dir), "--phase", "implement",
          "--cycle-id", f"{run_id}:1", "--expect-run-id", run_id]),
        (COHORT, cohort_state, "review record",
         ["review", "record", str(spec_dir), "--fingerprint", "a" * 40,
          "--expect-run-id", run_id]),
        (COHORT, cohort_state, "reset", ["reset", str(spec_dir)]),
        (ENGINE, engine_state, "transition",
         ["transition", str(spec_dir), "spec-ready"]),
        (ENGINE, engine_state, "reset", ["reset", str(spec_dir)]),
    ]

    for script, state_file, label, argv in cases:
        digest_before = state_file.read_bytes()
        lock = _plant_unacquirable(state_file)
        try:
            r = _run(script, *argv, cwd=repo)
        finally:
            lock.rmdir()
        if r.returncode == 0:
            fail("locked-verbs-refuse-when-held",
                 f"{label} exited 0 while the lock was held")
            return
        blob = r.stdout + r.stderr
        if "lock" not in blob.lower():
            fail("locked-verbs-refuse-when-held",
                 f"{label} refused but not for a lock reason: {blob.strip()[:160]!r}")
            return
        if state_file.read_bytes() != digest_before:
            fail("locked-verbs-refuse-when-held",
                 f"{label} modified {state_file.name} despite refusing")
            return

    # The two `init` verbs are exists-then-create, so they need a FRESH spec dir
    # or the refusal could come from "already exists" rather than the lock.
    for script, label, state_name, argv_for in (
        (COHORT, "cohort init", "state.json",
         lambda d: ["init", str(d), "--run-id", run_id]),
        (ENGINE, "engine init", "engine-state.json",
         lambda d: ["init", str(d), "--mode", "code"]),
    ):
        fresh = _make_spec_dir(repo, f"fresh-{label.split()[0]}")
        lock = _plant_unacquirable(fresh / state_name)
        try:
            r = _run(script, *argv_for(fresh), cwd=repo)
        finally:
            lock.rmdir()
        if r.returncode == 0:
            fail("locked-verbs-refuse-when-held",
                 f"{label} exited 0 while the lock was held")
            return
        if (fresh / state_name).exists():
            fail("locked-verbs-refuse-when-held",
                 f"{label} created {state_name} despite refusing")
            return

    # One CONTENDED case, so the timeout path is covered too and not just the
    # immediate-refusal path.
    digest_before = cohort_state.read_bytes()
    lock = _plant_contended(cohort_state)
    try:
        r = _run(COHORT, "record-attempt", str(spec_dir), "--phase", "implement",
                 "--cycle-id", f"{run_id}:9", "--expect-run-id", run_id, cwd=repo)
    finally:
        lock.unlink(missing_ok=True)
    if r.returncode == 0:
        fail("locked-verbs-refuse-when-held",
             "record-attempt exited 0 against a contended lock")
        return
    if "1234567" not in (r.stdout + r.stderr):
        fail("locked-verbs-refuse-when-held",
             f"contended refusal does not name the holder pid: {(r.stdout + r.stderr).strip()[:160]!r}")
        return
    if cohort_state.read_bytes() != digest_before:
        fail("locked-verbs-refuse-when-held",
             "record-attempt wrote state.json while contended")
        return
    ok("locked-verbs-refuse-when-held")


# ── AC16 — locked no-op paths still do not write ────────────────────────────

# STUB: AC16
def test_noop_paths_do_not_write(tmp: Path) -> None:
    """test-loop-cohort.sh:426-436 covers the unlocked read-only `status` verb
    and does NOT cover this: a LOCKED verb's early-return path must still leave
    the file byte-identical."""
    root = tmp / "noop"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    run_id = _engine_init(repo, spec_dir)
    state_file = spec_dir / "state.json"

    argv = ["record-attempt", str(spec_dir), "--phase", "implement",
            "--cycle-id", f"{run_id}:7", "--expect-run-id", run_id]
    first = _run(COHORT, *argv, cwd=repo)
    if first.returncode != 0:
        fail("noop-paths-do-not-write", f"first record-attempt failed: {first.stderr}")
        return
    before = state_file.read_bytes()
    second = _run(COHORT, *argv, cwd=repo)   # same cycle-id → idempotent no-op
    if second.returncode != 0:
        fail("noop-paths-do-not-write",
             f"repeated --cycle-id should be an idempotent no-op, got: {second.stderr}")
        return
    if state_file.read_bytes() != before:
        fail("noop-paths-do-not-write",
             "the idempotent record-attempt no-op rewrote state.json")
        return
    if lock_residue := list(spec_dir.glob("*.lock*")):
        fail("noop-paths-do-not-write", f"lock residue left behind: {lock_residue}")
        return

    # AC16's second clause: approve-plan re-run with both artifacts unchanged is
    # a no-op and must not rewrite the file either.
    first = _run(COHORT, "approve-plan", str(spec_dir),
                 "--expect-run-id", run_id, cwd=repo)
    if first.returncode != 0:
        fail("noop-paths-do-not-write",
             f"approve-plan failed: {(first.stdout + first.stderr).strip()[:200]}")
        return
    before_approve = state_file.read_bytes()
    again = _run(COHORT, "approve-plan", str(spec_dir),
                 "--expect-run-id", run_id, cwd=repo)
    if again.returncode != 0:
        fail("noop-paths-do-not-write",
             f"re-running approve-plan unchanged should be a no-op, got: "
             f"{(again.stdout + again.stderr).strip()[:200]}")
        return
    if state_file.read_bytes() != before_approve:
        fail("noop-paths-do-not-write",
             "approve-plan rewrote state.json when nothing had changed")
        return
    ok("noop-paths-do-not-write")


# ── AC10 — the lock-hold budget is machine-checked, not asserted in prose ──

# The canonical spawn set lives in `spawn_support`, imported by this file AND by
# the no-child-Python recorder, so a `check_call` or `os.system` added under the
# lock fails both scans. It used to be two independent literals in two files under
# a comment claiming they were shared; they were not, and both covered only the
# `subprocess` half.
SPAWN_ATTRS = ss.SUBPROCESS_ATTRS


def _locked_region_source(module_path):
    """`cmd_transition`'s body — the region that actually runs under the lock.

    NOT the syntactic `with sl.exclusive(...)` block: that lives in
    `_locked.decorate.wrapper` and contains only `return fn(args)`, an indirect call
    no AST walk can resolve. The decorator's own `_resolve_spec_dir` runs BEFORE the
    lock is taken and must not be counted.
    """
    import ast as _ast

    tree = _ast.parse(module_path.read_text(encoding="utf-8"))
    return next(n for n in _ast.walk(tree)
                if isinstance(n, _ast.FunctionDef) and n.name == "cmd_transition")


def _subprocess_edges_under_lock(module_path) -> int:
    """Count subprocess INVOCATION EDGES reachable from cmd_transition.

    Edges, not call sites. There is one `subprocess.run` site under the lock — in
    `_get_repo_root` — and `cmd_transition` reaches it twice: once through its own
    `_resolve_spec_dir`, once directly. Counting sites would give 1 and counting
    functions would give 2 for the wrong reason, so the walk resolves callees and
    sums their per-call subprocess counts.
    """
    import ast as _ast

    tree = _ast.parse(module_path.read_text(encoding="utf-8"))
    funcs = {n.name: n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}

    def walk_body(fn):
        """Walk a function's BODY only, never its decorator list.

        Load-bearing: `cmd_transition` is decorated `@_locked("transition")`, and
        `ast.walk` on the FunctionDef includes that decorator expression — so a naive
        walk descends into `_locked`, finds its `_resolve_spec_dir` call, and counts
        the one edge that runs BEFORE `sl.exclusive()` and must be excluded. It
        computed 3 instead of 2 until this was scoped to the body, which the test
        caught on its first run.
        """
        for stmt in fn.body:
            yield from _ast.walk(stmt)

    def direct(fn) -> int:
        return sum(
            1 for node in walk_body(fn)
            if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute)
            and isinstance(node.func.value, _ast.Name)
            and node.func.value.id == "subprocess" and node.func.attr in SPAWN_ATTRS
        )

    def edges(fn, seen: frozenset) -> int:
        total = direct(fn)
        for node in walk_body(fn):
            if not isinstance(node, _ast.Call):
                continue
            name = node.func.id if isinstance(node.func, _ast.Name) else None
            if name and name in funcs and name not in seen:
                total += edges(funcs[name], seen | {name})
        return total

    return edges(_locked_region_source(module_path), frozenset({"cmd_transition"}))


def test_lock_hold_budget() -> None:
    """timeout < max hold < stale_after, and the constant matches the real call graph.

    loop-engine holds the state lock across a read-decide-write section. An unbounded
    call makes the max hold unprovable; if the real hold can exceed stale_after, a
    merely-slow holder is judged dead, its lock is reclaimed, and a second writer is
    admitted — reinstating the lost update. Adding a guard must not be able to break
    that quietly, so every part of the bound is derived from source here.

    The constant-vs-source check is the new half. Before the guards moved in-process
    the constant was 6, a conservative bound over a measured five; a bound that is
    merely conservative goes stale silently, and a stale bound is how the inequality
    stops describing the code.
    """
    import ast as _ast

    for subject in (ENGINE, SCRIPT_DIR / "_loop_guards.py"):
        tree = _ast.parse(subject.read_text(encoding="utf-8"))
        unbounded = []
        for label, node in ss.spawn_calls(tree):
            # `os.*` primitives take no `timeout=` at all, so any one of them is
            # unbounded by construction — there is no bounded form to allow. Only
            # `subprocess.*` has a timeout to check for. Scanning the os half was
            # the gap: `os.system("git gc")` under the lock passed this test.
            if label.startswith("os."):
                unbounded.append(f"{label} at {subject.name}:{node.lineno} (unboundable)")
            elif not any(kw.arg == "timeout" for kw in node.keywords):
                unbounded.append(f"{label} at {subject.name}:{node.lineno}")
        if unbounded:
            fail("lock-hold-budget",
                 "process spawn(s) with no enforceable timeout reachable while the "
                 f"lock is held: {unbounded}. An unbounded call makes the maximum "
                 "hold unprovable against stale_after.")
            return

    # The guard layer must reach no spawning capability at all. A timeout scan cannot
    # see it: guard dispatch is indirect (`_GUARDS.get(...)` then `guard_fn(...)`)
    # through a module loaded at runtime, so absence is the only checkable property.
    guards_src = (SCRIPT_DIR / "_loop_guards.py").read_text(encoding="utf-8")
    guards_tree = _ast.parse(guards_src)
    spawn_refs = sorted({
        node.id for node in _ast.walk(guards_tree)
        if isinstance(node, _ast.Name) and node.id in ss.SPAWN_MODULES
    })
    if spawn_refs:
        fail("lock-hold-budget",
             f"_loop_guards.py reaches a spawning capability: {spawn_refs}. The guard "
             "layer runs inside the lock-holding process and must not be able to.")
        return

    # The arithmetic, read from the two modules rather than restated.
    engine = _load_module(ENGINE, "_engine_budget")
    sl = _load_module(SCRIPT_DIR / "_statelock.py", "_statelock_budget")
    max_hold = engine.SUBPROCESS_TIMEOUT_S * engine.MAX_SUBPROCESS_CALLS_UNDER_LOCK
    if not max_hold > sl.DEFAULT_TIMEOUT:
        fail("lock-hold-budget",
             f"statelock timeout ({sl.DEFAULT_TIMEOUT}s) must be shorter than the "
             f"max hold ({max_hold}s), or contenders give up on a live holder")
        return
    if not max_hold < sl.DEFAULT_STALE_AFTER:
        fail("lock-hold-budget",
             f"max hold ({max_hold}s) must be shorter than stale_after "
             f"({sl.DEFAULT_STALE_AFTER}s), or a live holder is reclaimed and a "
             "second writer admitted")
        return

    # And the constant must match the call graph, so it cannot go stale.
    edges = _subprocess_edges_under_lock(ENGINE)
    if edges != engine.MAX_SUBPROCESS_CALLS_UNDER_LOCK:
        fail("lock-hold-budget",
             f"MAX_SUBPROCESS_CALLS_UNDER_LOCK is "
             f"{engine.MAX_SUBPROCESS_CALLS_UNDER_LOCK} but {edges} subprocess "
             "invocation edge(s) are reachable from cmd_transition. A bound that no "
             "longer describes the call graph is how the inequality stops meaning "
             "anything — update both together.")
        return
    ok("lock-hold-budget")


def test_the_guard_path_cannot_reach_lint_spec_status_git_calls() -> None:
    """AC21's reachability half: `lint-spec-status.py` is not scanned file-wide.

    It imports `subprocess` and makes four `git` calls with no `timeout=`
    (`resolve_default_base_ref`, `base_spec_text`, `_repo_root`). Those are fine
    *because the guard path never invokes them* — and that claim is what needs an
    artifact, since `workspace.toml`'s deferral record cites this assertion by name
    as the reason the four calls are left unbounded.

    The guard path enters this module at exactly the symbols `_loop_guards.py`
    requires, so the roots are read from `_PARSER_SYMBOLS` rather than restated:
    a symbol added there widens this walk automatically.

    Vacuity is the real hazard, and the FIRST version of this test fell into it. It
    asserted only that no spawn was in the reachable set and that the spawning
    functions were disjoint from it — both trivially true when the walk resolves
    nothing, which is exactly what happens here: `parse_status` and
    `extract_status_token` call no other same-module function, so the reachable set
    IS the root set. Patching `reachable_from` to `return set()` left it green.

    So the artifact is a POSITIVE CONTROL plus the negative claim. `main()` demonstrably
    reaches all three spawning functions through a multi-hop walk; if the walker stops
    resolving edges, that assertion goes red and the negative result below stops being
    reported as meaningful. Without it, "the guard path reaches no spawn" is
    indistinguishable from "the walker found nothing at all".
    """
    import ast as _ast

    parser = SCRIPT_DIR / "lint-spec-status.py"
    tree = _ast.parse(parser.read_text(encoding="utf-8"))
    funcs = ss.functions_in(tree)

    spawning = {
        name for name, fn in funcs.items() if any(True for _ in ss.spawn_calls(fn))
    }
    if not spawning:
        fail("guard-path-reachability",
             f"no spawning function found in {parser.name} — the scan is not looking "
             "at what it thinks it is (did the spawn set or the file change?)")
        return

    # ── positive control: the walker really does resolve multi-hop edges ────
    # `main` is the CLI entry point and reaches every spawning function. This is the
    # assertion that makes the negative result below mean something.
    control = ss.reachable_from(tree, {"main"})
    missed = sorted(spawning - control)
    if missed:
        fail("guard-path-reachability",
             f"positive control failed: walking from main() did not reach {missed}, so "
             "the reachability walker is not resolving edges and the negative result "
             "below would be vacuous")
        return
    if len(control) < 5:
        fail("guard-path-reachability",
             f"positive control resolved only {len(control)} name(s) from main(); the "
             "walk has collapsed to something too shallow to trust")
        return

    # ── the negative claim ─────────────────────────────────────────────────
    guards = _load_module(SCRIPT_DIR / "_loop_guards.py", "_guards_reach")
    roots = set(guards._PARSER_SYMBOLS)
    callable_roots = roots & set(funcs)
    if not callable_roots:
        fail("guard-path-reachability",
             f"none of the required parser symbols {sorted(roots)} is a function in "
             f"{parser.name} — the walk would start nowhere and prove nothing")
        return

    reachable = ss.reachable_from(tree, callable_roots)
    offenders = sorted({
        f"{label} at {parser.name}:{node.lineno} (in {name}())"
        for name in reachable
        for label, node in ss.spawn_calls(funcs[name])
    })
    if offenders:
        fail("guard-path-reachability",
             f"the guard path reaches a process spawn in {parser.name}: {offenders}. "
             "AC21's deferral of the four unbounded git calls rests on them being "
             "unreachable; bound them or re-scope the criterion.")
        return
    ok("guard-path-reachability")


def test_only_git_runs_under_the_lock() -> None:
    """Every subprocess reachable under the lock is git, by argv inspection.

    Complements the count: two bounded edges would still be wrong if one of them had
    become something other than git.
    """
    import ast as _ast

    src = ENGINE.read_text(encoding="utf-8")
    tree = _ast.parse(src)
    non_git = []
    for node in _ast.walk(tree):
        if not (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute)
                and isinstance(node.func.value, _ast.Name)
                and node.func.value.id == "subprocess"):
            continue
        if not node.args:
            non_git.append(f"line {node.lineno}: no argv")
            continue
        argv = node.args[0]
        first = argv.elts[0] if isinstance(argv, (_ast.List, _ast.Tuple)) and argv.elts else None
        if not (isinstance(first, _ast.Constant) and first.value == "git"):
            non_git.append(f"line {node.lineno}: argv[0] is not 'git'")
    if non_git:
        fail("only-git-under-lock", f"non-git subprocess under the lock: {non_git}")
        return
    ok("only-git-under-lock")


# ── AC18 — every child resolves its throwaway repo ─────────────────────────

# STUB: AC21
def test_harness_is_hermetic(tmp: Path) -> None:
    """Every child resolves and writes only its throwaway git repository."""
    root = tmp / "herm"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    _engine_init(repo, spec_dir)
    res, ready, contended, unlocked_writes, roots, timed_out = _run_barriered(
        2,
        ENGINE,
        [["transition", str(spec_dir), "spec-ready"]] * 2,
        repo,
    )
    if not _check_contention(
        "harness-is-hermetic",
        2,
        ready,
        contended,
        unlocked_writes,
        roots,
        timed_out,
        repo,
    ):
        return

    if not (repo / ".loop-run").is_dir():
        fail("harness-is-hermetic",
             "the tmp repo has no .loop-run/ — the child did not resolve its "
             "repo root inside tmp_path, so the run was not hermetic")
        return

    winners = [r for r in res if r[0] == 0]
    if len(winners) != 1:
        detail = " | ".join(
            f"rc={rc} {(so + se).strip()[:160]!r}" for rc, so, se in res
        )
        fail(
            "harness-is-hermetic",
            f"throwaway transition had {len(winners)} winners, expected 1: {detail}",
        )
        return
    ok("harness-is-hermetic")
