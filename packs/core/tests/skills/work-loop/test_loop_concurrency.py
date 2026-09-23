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

import ast as _ast_mod
import contextlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
import spawn_support as ss

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
    about whether each verb was actually wrapped. All ELEVEN locked verbs."""
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
        (COHORT, cohort_state, "dispatch-receipt",
         ["dispatch-receipt", str(spec_dir), "--task", "T1", "--wave-index", "0",
          "--receipt", "--expect-run-id", run_id]),
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
    """The CLI self-test covers the unlocked read-only ``status`` verb.

    It does not cover this: a locked verb's early-return path must still leave
    the file byte-identical.
    """
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

    Its Git calls are outside the engine's locked call graph. This assertion proves
    that reachability boundary only: it does not scan `lint-spec-status.py` for
    `timeout=` and must not grow into a separate lint gate.

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
    reaches every spawning function through a multi-hop walk; if the walker stops
    resolving edges, that assertion goes red and the negative result below stops being
    reported as meaningful. The count is not hardcoded — `spawning` is derived, so a
    fourth git-calling function is covered automatically. Without it, "the guard path reaches no spawn" is
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


# ══ cohort-state identity: structure asserted from source ══════════════════
#
# Spec: docs/specs/wave-exit-verdict-serialisation/spec.md AC1, AC3, AC5, AC6,
# AC7, AC15, AC16, AC22.
#
# These are static because what they pin is where code sits, and no runtime
# observation can see that: `_release` unlinks the lockfile on every normal
# exit, so a post-run probe reports the same absence whether the lock was taken
# or never taken at all.

def _engine_tree():
    return _ast_mod.parse(ENGINE.read_text(encoding="utf-8"))


def _fn(tree, name: str):
    return next(n for n in _ast_mod.walk(tree)
                if isinstance(n, _ast_mod.FunctionDef) and n.name == name)


def _called_names(node) -> list[str]:
    """Every called name in source order: bare names and attribute tails."""
    out = []
    for n in _ast_mod.walk(node):
        if isinstance(n, _ast_mod.Call):
            f = n.func
            if isinstance(f, _ast_mod.Name):
                out.append(f.id)
            elif isinstance(f, _ast_mod.Attribute):
                out.append(f.attr)
    return out


def _stmt_index_of_call(fn, callee: str) -> int:
    """Index of the top-level statement in `fn` containing a call to `callee`."""
    for i, stmt in enumerate(fn.body):
        if callee in _called_names(stmt):
            return i
    raise AssertionError(f"{callee} is not called in {fn.name}")


def test_cohort_fingerprint_capture_precedes_every_other_call() -> None:
    """AC1: nothing in cmd_transition can read cohort state before the capture.

    Positional, not a call-graph walk. The guard dispatch is
    `_GUARDS.get(...)` then `guard_fn(...)`, and the `_guards()` calls are
    attribute calls on a module loaded at runtime, so the read set is not
    statically decidable — this file already records that verdict elsewhere.
    What IS decidable is that the capture comes first, which dominates any read
    a later edit adds wherever it adds it.
    """
    fn = _fn(_engine_tree(), "cmd_transition")
    capture_at = _stmt_index_of_call(fn, "_cohort_fingerprint")
    # Named individually, not "any builtin": `getattr` and friends can reach
    # anything, and the point of this check is that nothing before the capture
    # can touch cohort state. `str` is the exception-message conversion in the
    # spec-dir resolution's own handler.
    allowed_before = {"_resolve_spec_dir", "stop", "str"}
    earlier = set()
    for stmt in fn.body[:capture_at]:
        earlier.update(_called_names(stmt))
    assert earlier <= allowed_before, (
        f"calls precede the cohort-state capture in cmd_transition: "
        f"{sorted(earlier - allowed_before)}. Any of them could read cohort "
        f"state, which would leave the capture describing a state the "
        f"transition had already acted on."
    )


def test_commit_writes_appear_exactly_once_in_cmd_transition() -> None:
    """AC5: one commit path, so a checked and an unchecked copy cannot drift."""
    fn = _fn(_engine_tree(), "cmd_transition")
    names = _called_names(fn)
    for callee in ("_write_events_pending", "_write_engine_state_atomic"):
        assert names.count(callee) == 1, (
            f"{callee} appears {names.count(callee)} times in cmd_transition; "
            "a second commit path would not be covered by the identity check"
        )


def _commit_hold_node(fn):
    """The `with _cohort_commit_hold(...)` statement inside cmd_transition."""
    for n in _ast_mod.walk(fn):
        if isinstance(n, (_ast_mod.With, _ast_mod.AsyncWith)):
            for item in n.items:
                if "_cohort_commit_hold" in _called_names(item.context_expr):
                    return n
    raise AssertionError("cmd_transition has no `with _cohort_commit_hold(...)`")


def test_cohort_hold_contains_the_commit_and_nothing_that_decides_it() -> None:
    """AC6: the hold spans the re-read and both writes, and nothing else that matters.

    The exclusions are not stylistic. `apply_contract_amendment` takes the
    cohort lock itself on a lock that is not reentrant, so enclosing it would
    self-deadlock; the guard evaluations and the pre-guard must stay outside or
    the hold grows without bound.
    """
    fn = _fn(_engine_tree(), "cmd_transition")
    inside = set(_called_names(_commit_hold_node(fn)))

    for required in ("_revalidate_cohort_state", "_write_events_pending",
                     "_write_engine_state_atomic"):
        assert required in inside, f"{required} must be inside the cohort hold"

    # All six AC6 names, not the four that were easy: the FSM table lookup and
    # the outbox unlink were missing, and a check that omits an exclusion the
    # criterion states cannot fail on the case the criterion was written for.
    for excluded in ("_schedule_check_current", "guard_fn", "_append_events_jsonl",
                     "apply_contract_amendment", "_run_id_preflight",
                     "unlink", "_events_pending_path", "get"):
        assert excluded not in inside, (
            f"{excluded} is inside the cohort hold; the hold must cover the "
            "commit only"
        )


def test_cohort_acquisition_is_not_swallowed_by_a_continuing_handler() -> None:
    """AC7: outside the body AND the handler of any try whose handler continues.

    The pending write sits in a `try` whose `except Exception` warns and falls
    through to the unconditional state write. An acquisition placed in that
    BODY — not just in the handler — is swallowed and becomes an unlocked
    commit on a lock failure, which is why this checks both.
    """
    fn = _fn(_engine_tree(), "cmd_transition")
    hold = _commit_hold_node(fn)

    def handler_continues(handler) -> bool:
        last = handler.body[-1] if handler.body else None
        return not isinstance(last, (_ast_mod.Return, _ast_mod.Raise,
                                     _ast_mod.Continue, _ast_mod.Break))

    for node in _ast_mod.walk(fn):
        if not isinstance(node, _ast_mod.Try):
            continue
        if not any(handler_continues(h) for h in node.handlers):
            continue
        for region in (node.body, *[h.body for h in node.handlers]):
            for stmt in region:
                assert hold not in list(_ast_mod.walk(stmt)), (
                    "the cohort-lock acquisition sits inside a try whose "
                    "handler continues after catching; a lock failure there is "
                    "swallowed and falls through to the unlocked state write"
                )


def test_the_exemption_is_read_from_the_declared_set() -> None:
    """AC3: the branch consults the set, so a hard-coded literal cannot pass.

    A module constant equal to {"contract-amendment"} is true whether or not
    anything reads it; what must hold is that the decision points consult it.
    """
    tree = _engine_tree()
    for fname in ("_cohort_commit_hold", "_revalidate_cohort_state"):
        src = _ast_mod.dump(_fn(tree, fname))
        assert "_FINGERPRINT_EXEMPT_EVENTS" in src, (
            f"{fname} must decide the exemption from the declared set"
        )
        assert "'contract-amendment'" not in src, (
            f"{fname} compares against a hard-coded event literal; a second "
            "hard-coded exemption would then pass the set assertion untouched"
        )


def _cohort_tree():
    return _ast_mod.parse(COHORT.read_text(encoding="utf-8"))


def _decorator_names(fn) -> set[str]:
    out = set()
    for d in fn.decorator_list:
        node = d.func if isinstance(d, _ast_mod.Call) else d
        if isinstance(node, _ast_mod.Name):
            out.add(node.id)
        elif isinstance(node, _ast_mod.Attribute):
            out.add(node.attr)
    return out


_WITH_STATE_LOCK = "<with_state_lock>"


def _with_state_lock_targets(tree) -> dict[str, set[str]]:
    """Body callables handed to `with_state_lock(...)`, and the Call nodes doing it."""
    targets: set[str] = set()
    sites: set[int] = set()
    for n in _ast_mod.walk(tree):
        if not (isinstance(n, _ast_mod.Call) and "with_state_lock" in _called_names(n)):
            continue
        sites.add(id(n))
        # The body callable is the third positional, or the `body` keyword —
        # not every `Name` in the call. `with_state_lock(spec_dir, verb, body)`
        # would otherwise yield `spec_dir` and `verb` as targets, and a module
        # function that ever shared one of those names would be granted
        # heldness it never earned.
        candidates = list(n.args[2:3])
        candidates += [kw.value for kw in n.keywords if kw.arg == "body"]
        for arg in candidates:
            if isinstance(arg, _ast_mod.Lambda):
                targets |= set(_called_names(arg.body))
            elif isinstance(arg, _ast_mod.Name):
                targets.add(arg.id)
    return {"targets": targets, "sites": sites}


def _cohort_lock_held_functions() -> set[str]:
    """Every `loop-cohort.py` function whose body runs under the cohort lock.

    Three shapes, and a check that knows only the first two reds on the third:
      1. the `@_locked` decorator, which seven verbs use;
      2. the inline `with sl.exclusive(...)` in `apply_contract_amendment`;
      3. a body callable handed to `with_state_lock(...)` — the ONLY route
         holding `_schedule_run_impl`'s write.
    Shape 3 is why `loop-cohort.py` has just two literal `exclusive(` sites
    while far more code runs held: keying on the literal alone would miss the
    majority.

    Heldness is per PATH. A shape-3 target is NOT seeded as a root: its
    heldness is a property of the `with_state_lock` call site, not of its own
    body, so seeding it would exempt it from the every-caller rule and let an
    unlocked second route to the same write pass unchallenged. The call site is
    instead recorded as one held caller, and the target must earn heldness like
    anything else — every caller held, at least one caller.
    """
    tree = _cohort_tree()
    funcs = {n.name: n for n in _ast_mod.walk(tree)
             if isinstance(n, _ast_mod.FunctionDef)}
    ws = _with_state_lock_targets(tree)

    held = {name for name, fn in funcs.items() if "_locked" in _decorator_names(fn)}
    held |= {name for name, fn in funcs.items()
             if any("exclusive" in _called_names(item.context_expr)
                    for w in _ast_mod.walk(fn)
                    if isinstance(w, _ast_mod.With) for item in w.items)}
    held.add(_WITH_STATE_LOCK)

    callers: dict[str, set[str]] = {name: set() for name in funcs}
    for name, fn in funcs.items():
        for node in _ast_mod.walk(fn):
            if not isinstance(node, _ast_mod.Call):
                continue
            f = node.func
            callee = f.id if isinstance(f, _ast_mod.Name) else (
                f.attr if isinstance(f, _ast_mod.Attribute) else None)
            if callee in callers:
                callers[callee].add(name)
    # Attribute a shape-3 target's invocation to the lock site, not to the
    # function that merely passes the callable in — the passer is unheld.
    for target in ws["targets"]:
        if target in callers:
            # Keep only callers that reach the target OUTSIDE the lock site —
            # those are the genuinely unheld routes. The function that merely
            # hands the callable to `with_state_lock` is not one of them.
            callers[target] = {c for c in callers[target]
                               if target in _called_names_outside_ws(funcs.get(c), ws)}
            callers[target].add(_WITH_STATE_LOCK)

    changed = True
    while changed:
        changed = False
        for name in funcs:
            if name in held:
                continue
            who = callers[name]
            if who and who <= held:
                held.add(name)
                changed = True
    return held


def _called_names_outside_ws(fn, ws) -> list[str]:
    """Calls in `fn` excluding those inside a `with_state_lock(...)` argument."""
    if fn is None:
        return []
    inside: set[int] = set()
    for n in _ast_mod.walk(fn):
        if isinstance(n, _ast_mod.Call) and id(n) in ws["sites"]:
            for sub in _ast_mod.walk(n):
                inside.add(id(sub))
    return [c for node in _ast_mod.walk(fn)
            if isinstance(node, _ast_mod.Call) and id(node) not in inside
            for c in _called_names(node)]


def test_every_cohort_state_write_runs_inside_a_cohort_hold() -> None:
    """AC17: the premise the whole identity check rests on.

    If a cohort writer ever ran unlocked, the engine's re-read could observe
    state no lock protected and commit against it with every other criterion
    still green. AC18 pins only the converse direction, so without this the
    foundational assumption is asserted by prose alone.
    """
    tree = _cohort_tree()
    held = _cohort_lock_held_functions()
    offenders = []
    for fn in _ast_mod.walk(tree):
        if not isinstance(fn, _ast_mod.FunctionDef):
            continue
        names = _called_names(fn)
        writes = "write_state_atomic" in names
        unlinks = "unlink" in names and "state_path_for" in names
        if (writes or unlinks) and fn.name not in held:
            offenders.append(fn.name)
    assert not offenders, (
        f"these write or unlink cohort state.json outside any cohort-lock "
        f"hold: {sorted(offenders)}. Exempting one here would blind the check "
        f"to the exact path it exists for — fix the hold, not the list."
    )


def test_loop_cohort_never_reaches_the_engine_lock_or_engine_state() -> None:
    """AC18: the one-way acquisition order, checked rather than observed.

    The nested hold's deadlock argument depends on this and nothing states it:
    `loop-cohort.py:2427` says the module never reads `engine-state.json`,
    which is this property, not the ordering. The ordering rests on the call
    sites alone, so it needs a check that reds when one moves.
    """
    src = COHORT.read_text(encoding="utf-8")
    tree = _cohort_tree()
    for n in _ast_mod.walk(tree):
        if isinstance(n, _ast_mod.Call) and "exclusive" in _called_names(n):
            locked = _ast_mod.dump(n)
            assert "engine" not in locked.lower(), (
                f"loop-cohort acquires a lock on an engine path: {locked[:200]}"
            )
    code_lines = [
        line for line in src.splitlines()
        if "engine-state" in line and not line.lstrip().startswith("#")
    ]
    assert not code_lines, (
        f"loop-cohort reads or names engine-state outside a comment: {code_lines}"
    )


def test_cohort_commit_hold_reaches_no_spawn_and_stays_under_the_timeout() -> None:
    """AC22: the only hold this delivery creates, bounded by a number with an origin.

    AC6's exclusion list cannot bound it — an exhaustive negative list passes
    any operation nobody thought to enumerate. This asserts the positive
    property instead: nothing inside can spawn, so the hold is local I/O, and
    the declared ceiling sits below the acquisition timeout. Above that timeout
    a contending cohort verb abandons a holder that was about to release.
    """
    engine = _load_module(ENGINE, "_engine_hold_budget")
    sl = _load_module(SCRIPT_DIR / "_statelock.py", "_statelock_hold_budget")
    tree = _engine_tree()
    # Rooted at the `with` block's own statements, not at three helpers. The
    # two operations this delivery MOVED INTO the hold — the pending write and
    # the state write — are called from cmd_transition's with-body, so a set
    # built from the helpers alone leaves the ceiling unverified for exactly
    # the code it is meant to bound.
    hold_body = _commit_hold_node(_fn(tree, "cmd_transition"))
    reachable = set(_called_names(hold_body))
    funcs_e = {n.name: n for n in _ast_mod.walk(tree)
               if isinstance(n, _ast_mod.FunctionDef)}
    frontier, seen = list(reachable), set(reachable)
    while frontier:
        fn = funcs_e.get(frontier.pop())
        if fn is None:
            continue
        for callee in _called_names(fn):
            if callee not in seen:
                seen.add(callee)
                frontier.append(callee)
    reachable = seen
    assert not (reachable & set(SPAWN_ATTRS)), (
        f"the cohort hold reaches a spawning capability: "
        f"{sorted(reachable & set(SPAWN_ATTRS))}"
    )
    assert 0 < engine.COHORT_COMMIT_HOLD_MAX_S < sl.DEFAULT_TIMEOUT, (
        f"the inner hold's ceiling ({engine.COHORT_COMMIT_HOLD_MAX_S}s) must sit "
        f"below the acquisition timeout ({sl.DEFAULT_TIMEOUT}s), or a contending "
        f"cohort verb times out against a live holder"
    )


def _reaches_a_cohort_acquisition(name: str) -> bool:
    """Does this `loop-cohort` function, or anything it calls, take the lock?

    DOWNWARD reachability. Not `held`, which after the per-path repair means
    "always called from inside a hold" — the inverse relation. Using `held`
    here counted a pure argv parser as acquiring, and would have kept passing
    if the one genuinely acquiring mutator stopped acquiring.
    """
    tree = _cohort_tree()
    funcs = {n.name: n for n in _ast_mod.walk(tree)
             if isinstance(n, _ast_mod.FunctionDef)}

    def acquires_directly(fn) -> bool:
        if "_locked" in _decorator_names(fn):
            return True
        names = _called_names(fn)
        return "exclusive" in names or "with_state_lock" in names

    seen, frontier = set(), [name]
    while frontier:
        current = frontier.pop()
        fn = funcs.get(current)
        if fn is None or current in seen:
            continue
        seen.add(current)
        if acquires_directly(fn):
            return True
        frontier.extend(c for c in _called_names(fn) if c in funcs)
    return False


def _engine_reachable_functions() -> set[str]:
    """Functions in `loop-engine.py` reachable from `cmd_transition` by name.

    Bare-name callees only. That is the limit of what a static walk can do here
    and it is stated rather than papered over: a call through an attribute on a
    runtime-loaded module is invisible to it.
    """
    tree = _engine_tree()
    funcs = {n.name: n for n in _ast_mod.walk(tree)
             if isinstance(n, _ast_mod.FunctionDef)}
    seen, frontier = {"cmd_transition"}, ["cmd_transition"]
    while frontier:
        fn = funcs.get(frontier.pop())
        if fn is None:
            continue
        for node in _ast_mod.walk(fn):
            if isinstance(node, _ast_mod.Call) and isinstance(node.func, _ast_mod.Name):
                name = node.func.id
                if name in funcs and name not in seen:
                    seen.add(name)
                    frontier.append(name)
    return seen


def _engine_cohort_acquisition_sites() -> tuple[int, list[str]]:
    """Count COHORT acquisition SITES reachable from `cmd_transition`.

    Sites, not containing-function names. A set of names cannot rise when a
    second acquisition is added inside a function already in it, and the bound
    consumes this as a count of acquisitions — so a name set silently
    under-derives by a whole timeout.

    Every `exclusive(...)` site must land in a bucket. One whose argument names
    neither the cohort path helper nor the engine-state path is returned as
    unclassified and fails the caller, because dropping it is the fail-open
    direction: an acquisition written through a local variable or a new wrapper
    would leave the count unchanged.
    """
    tree = _engine_tree()
    reachable = _engine_reachable_functions()
    cohort, unclassified = 0, []
    for fn in _ast_mod.walk(tree):
        if not isinstance(fn, _ast_mod.FunctionDef) or fn.name not in reachable:
            continue
        for node in _ast_mod.walk(fn):
            if not (isinstance(node, _ast_mod.Call)
                    and isinstance(node.func, _ast_mod.Attribute)
                    and node.func.attr == "exclusive"):
                continue
            arg = " ".join(_ast_mod.dump(a) for a in node.args)
            names_cohort = "state_path_for" in arg or "state.json" in arg
            names_engine = "_engine_state_path" in arg or "engine-state.json" in arg
            if names_engine and not names_cohort:
                continue
            if names_cohort:
                cohort += 1
            else:
                unclassified.append(f"{fn.name}:{node.lineno}")
    return cohort, unclassified


def _cohort_mutator_acquisition_sites() -> tuple[int, set[str]]:
    """Count `_cohort_mutator().<fn>(` SITES whose target reaches an acquisition."""
    acquiring, sites = set(), 0
    for n in _ast_mod.walk(_engine_tree()):
        if not isinstance(n, _ast_mod.Call):
            continue
        f = n.func
        if (isinstance(f, _ast_mod.Attribute) and isinstance(f.value, _ast_mod.Call)
                and "_cohort_mutator" in _called_names(f.value)
                and _reaches_a_cohort_acquisition(f.attr)):
            acquiring.add(f.attr)
            sites += 1
    return sites, acquiring


def test_engine_lock_budget_counts_its_cohort_acquisitions() -> None:
    """AC15: the derived bound describes the code, including nested acquisitions.

    `test_lock_hold_budget` above counts subprocess edges only, so it sees no
    lock acquisition at all — not this delivery's, and not the two that already
    ship. A bound that cannot see a ten-second wait is the silent staleness that
    test's own message warns about.

    The count is the MAXIMUM over mutually exclusive branches, not their sum:
    `contract-amendment` is the only event that acquires through its effect and
    the only event exempt from the identity check, so at most one cohort
    acquisition is live on any single path.
    """
    engine = _load_module(ENGINE, "_engine_acq_budget")
    sl = _load_module(SCRIPT_DIR / "_statelock.py", "_statelock_acq_budget")

    # Two mutually exclusive groups, both counted by SITE rather than by
    # containing function. `contract-amendment` is the only event that acquires
    # through its effect and the only event exempt from the identity check, so
    # at most one group is live on any single path.
    engine_sites, unclassified = _engine_cohort_acquisition_sites()
    mutator_sites, acquiring = _cohort_mutator_acquisition_sites()
    assert not unclassified, (
        f"these `exclusive(...)` sites reachable from cmd_transition lock a path "
        f"the classifier cannot attribute: {unclassified}. Dropping one is the "
        f"fail-open direction — it would leave the derived bound unchanged."
    )
    assert engine_sites == 1, (
        f"engine-side cohort acquisition sites: {engine_sites}, expected 1. "
        "Re-derive the bound rather than widening this assertion."
    )
    assert (mutator_sites, acquiring) == (2, {"apply_contract_amendment"}), (
        f"acquiring cohort-mutator sites changed: {mutator_sites} site(s) across "
        f"{sorted(acquiring)}. Re-derive the bound rather than widening this."
    )

    concurrent = max(engine_sites, mutator_sites)
    max_hold = (engine.SUBPROCESS_TIMEOUT_S * engine.MAX_SUBPROCESS_CALLS_UNDER_LOCK
                + sl.DEFAULT_TIMEOUT * concurrent)
    assert sl.DEFAULT_TIMEOUT < max_hold < sl.DEFAULT_STALE_AFTER, (
        f"engine-lock budget broken: timeout={sl.DEFAULT_TIMEOUT}s "
        f"max_hold={max_hold}s stale_after={sl.DEFAULT_STALE_AFTER}s"
    )


def test_cohort_lock_holders_are_bounded_below_stale_after() -> None:
    """AC16: the lock this design newly depends on, which no budget check reached.

    The engine's correctness now rests on the cohort lock excluding cohort
    writers for the duration of its hold. An unbounded spawn added under
    `@_locked("schedule")` would push a cohort hold past `stale_after`, get the
    lock reclaimed while a live writer is inside it, and make the engine's
    re-read observe state no lock protected — with every other gate green.
    """
    sl = _load_module(SCRIPT_DIR / "_statelock.py", "_statelock_cohort_budget")
    tree = _cohort_tree()
    held = _cohort_lock_held_functions()

    # Boundedness, not absence. `_get_repo_root` IS reachable under the hold —
    # every `@_locked` verb re-calls `_resolve_spec_dir` in its own body,
    # redundantly with the decorator — and it is harmless only because that
    # resolver memoises per working directory, so the in-hold call is a cache
    # hit. Asserting "no spawn" would therefore be false about the code; what
    # must hold is that every reachable spawn is bounded, which is how the
    # engine-side budget above reasons too.
    cohort = _load_module(COHORT, "_loop_cohort_budget")
    funcs_all = {n.name: n for n in _ast_mod.walk(tree)
                 if isinstance(n, _ast_mod.FunctionDef)}
    unbounded = []
    spawn_edges = 0
    for name in sorted(held):
        fn = funcs_all.get(name)
        if fn is None:
            continue
        for node in _ast_mod.walk(fn):
            if not (isinstance(node, _ast_mod.Call)
                    and isinstance(node.func, _ast_mod.Attribute)
                    and isinstance(node.func.value, _ast_mod.Name)
                    and node.func.value.id == "subprocess"
                    and node.func.attr in SPAWN_ATTRS):
                continue
            spawn_edges += 1
            if not any(kw.arg == "timeout" for kw in node.keywords):
                unbounded.append(f"{name}: subprocess.{node.func.attr}")
    assert not unbounded, (
        f"unbounded spawn under the cohort lock: {unbounded}. An unbounded "
        f"call here makes the maximum hold unprovable, and a hold past "
        f"`stale_after` gets the lock reclaimed while a live writer is inside."
    )

    engine = _load_module(ENGINE, "_engine_cohort_budget")
    cohort_max_hold = cohort.GIT_TIMEOUT_S * spawn_edges + engine.COHORT_COMMIT_HOLD_MAX_S
    assert cohort_max_hold < sl.DEFAULT_STALE_AFTER, (
        f"cohort holders can run {cohort_max_hold}s against a "
        f"{sl.DEFAULT_STALE_AFTER}s staleness budget"
    )


# ══ the race itself, across two real processes ═════════════════════════════
#
# Spec: docs/specs/wave-exit-verdict-serialisation/spec.md AC4, AC11, AC12.
#
# The rendezvous is forced, not hoped for. Child A runs a real engine
# transition and blocks immediately after its cohort-state capture; child B
# runs a real cohort mutator and signals when it has committed; only then does
# A proceed to its commit. Scheduler luck decides nothing, so a pass means the
# interleaving genuinely occurred rather than that the two happened to overlap.

_CAPTURE_CHILD_SRC = '''
import importlib.util, sys, time
from pathlib import Path
probe = Path(sys.argv[1]); target = sys.argv[2]; argv = sys.argv[3:]

spec = importlib.util.spec_from_file_location("_subject", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Rendezvous at the ACQUISITION, not at the capture. Once the engine holds the
# cohort lock the mutator cannot commit at all, so the only window the real
# defect has is between the guard's verdict and the acquisition. Pausing at the
# capture instead would let the mutator land BEFORE the guard ran, which is a
# different and much less interesting interleaving.
real_hold = mod._cohort_commit_hold

def probed(spec_dir, event):
    (probe / "guarded").write_text(event, encoding="utf-8")
    deadline = time.monotonic() + 60.0
    while not (probe / "mutated").exists():
        if time.monotonic() >= deadline:
            raise RuntimeError("timed out waiting for the mutator to commit")
        time.sleep(0.005)
    return real_hold(spec_dir, event)

mod._cohort_commit_hold = probed
sys.exit(mod.main(argv))
'''

_MUTATOR_CHILD_SRC = '''
import importlib.util, sys, time
from pathlib import Path
probe = Path(sys.argv[1]); target = sys.argv[2]; argv = sys.argv[3:]

spec = importlib.util.spec_from_file_location("_subject", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

deadline = time.monotonic() + 60.0
while not (probe / "guarded").exists():
    if time.monotonic() >= deadline:
        raise RuntimeError("timed out waiting for the engine to reach its commit")
    time.sleep(0.005)

rc = mod.main(argv)
(probe / "mutated").write_text(str(rc), encoding="utf-8")
sys.exit(rc)
'''


def _run_interleaved(repo: Path, engine_argv: list[str], mutator_argvs: list[list[str]]):
    """Engine transition and cohort mutator(s), rendezvoused at the capture.

    Deliberately a sibling of `_run_barriered` rather than a change to it:
    that helper hands ONE target module to every child and hardwires its child
    source, and its four existing callers depend on both.
    """
    probe = repo / "_pair"
    if probe.exists():
        for stale in probe.iterdir():
            stale.unlink()
    else:
        probe.mkdir()

    cap = repo / "_capture_child.py"
    cap.write_text(_CAPTURE_CHILD_SRC, encoding="utf-8")
    mut = repo / "_mutator_child.py"

    engine_proc = subprocess.Popen(
        [sys.executable, str(cap), str(probe), str(ENGINE), *engine_argv],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", cwd=str(repo),
    )
    # Every mutation runs in ONE child, in order, so a multi-step mutation
    # (reset, init, schedule) lands entirely inside the window rather than
    # racing itself. `__write_plan__` is not a cohort verb: it repartitions the
    # plan so a following `schedule` genuinely changes cohort state, which is
    # what makes the schedule cases non-vacuous.
    mut.write_text(
        _MUTATOR_CHILD_SRC.replace(
            "rc = mod.main(argv)",
            "rc = 0\n"
            "for _step in argv[0].split('\\x1f'):\n"
            "    _a = _step.split('\\x1e')\n"
            "    if _a[0] == '__write_plan__':\n"
            "        Path(_a[1]).write_text(_a[2], encoding='utf-8')\n"
            "        continue\n"
            "    rc = mod.main(_a)\n"
            "    if rc != 0:\n"
            "        break",
        ),
        encoding="utf-8",
    )
    script = mut
    mutator_args = ["\x1f".join("\x1e".join(a) for a in mutator_argvs)]

    mutator_proc = subprocess.Popen(
        [sys.executable, str(script), str(probe), str(COHORT), *mutator_args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", cwd=str(repo),
    )
    e_out, e_err = engine_proc.communicate(timeout=HARNESS_PROCESS_TIMEOUT)
    m_out, m_err = mutator_proc.communicate(timeout=HARNESS_PROCESS_TIMEOUT)
    return (engine_proc.returncode, e_out, e_err), (mutator_proc.returncode, m_out, m_err), probe


def _code_implementation_run(repo: Path, name: str, tasks: str = "T1\nT2"):
    """Drive a real run to CODE-IMPLEMENTATION with a two-wave schedule."""
    spec_dir = repo / "docs" / "specs" / name
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text("- **Status:** Approved\n", encoding="utf-8")
    plan = "# Plan\n\n- **Status:** Approved\n\n"
    plan += "\n".join(
        f"### {t}\n\n**Depends on:** " + ("none" if i == 0 else f"T{i}") + "\n"
        for i, t in enumerate(tasks.split("\n"))
    )
    (spec_dir / "plan.md").write_text(plan, encoding="utf-8")

    r = _run(ENGINE, "init", str(spec_dir), "--mode", "code", "--json", cwd=repo)
    assert r.returncode == 0, r.stderr
    run_id = json.loads(r.stdout)["run_id"]
    assert _run(COHORT, "init", str(spec_dir), "--run-id", run_id, cwd=repo).returncode == 0
    for event in ("spec-ready", "reviewers-clean", "spec-approved", "plan-approved"):
        r = _run(ENGINE, "transition", str(spec_dir), event, cwd=repo)
        assert r.returncode == 0, f"{event}: {r.stderr}"
    for verb in (("approve-plan",), ("schedule",)):
        r = _run(COHORT, *verb, str(spec_dir), "--expect-run-id", run_id, cwd=repo)
        assert r.returncode == 0, f"{verb}: {r.stderr}"
    r = _run(ENGINE, "transition", str(spec_dir), "plan-locked", cwd=repo)
    assert r.returncode == 0, r.stderr
    return spec_dir, run_id


def _receipt(repo: Path, spec_dir: Path, run_id: str, task: str, wave: int) -> None:
    r = _run(COHORT, "dispatch-receipt", str(spec_dir), "--task", task,
             "--wave-index", str(wave), "--receipt", "--expect-run-id", run_id, cwd=repo)
    assert r.returncode == 0, r.stderr


def _assert_refused_without_writing(engine_res, mutator_res, probe, spec_dir,
                                    before, before_cohort):
    rc, out, err = engine_res
    m_rc, _, m_err = mutator_res
    assert (probe / "guarded").exists(), "the engine never reached its commit"
    assert (probe / "mutated").exists(), "the mutator never ran"
    assert m_rc == 0, f"the mutator must succeed for the race to exist: {m_err}"
    # Prove the race was real before asserting the refusal. A mutator that
    # rewrote identical content moves nothing, and a test that skipped this
    # would pass against a no-op and report a closed race that never opened.
    after_state = (spec_dir / "state.json").read_text(encoding="utf-8")
    assert json.loads(after_state) != json.loads(before_cohort), (
        "the mutator left cohort state unchanged, so this case exercises no race"
    )
    assert rc != 0, f"the transition committed against moved cohort state: {out}{err}"
    assert (spec_dir / "engine-state.json").read_bytes() == before, (
        "engine-state.json changed on a refused transition"
    )
    pending = list((spec_dir.parents[2] / ".loop-run").glob("events.pending"))
    assert not pending, f"a pending record survived a refused transition: {pending}"


@pytest.mark.parametrize(
    "case,mutators",
    [
        ("wave-advance", [["wave", "advance", "--from-index", "0"]]),
        ("schedule", [["schedule"]]),
        ("reset-init-schedule", [["reset"], ["init"], ["schedule"]]),
    ],
)
def test_wave_complete_refuses_a_mutation_in_its_commit_window(
    tmp: Path, case: str, mutators: list[list[str]]
) -> None:
    """AC11/AC12: a real cohort mutator commits between the guard and the commit.

    Three mutators, one predicate. `wave advance` moves the pointer;
    `schedule` repartitions and can leave the pointer where the guard read it,
    which is the case a pointer-only check would miss; `reset`+`init`+
    `schedule` changes the cohort `run_id` while every guard verdict still
    approves, which is the case a guard-derived check would miss because the
    run-id preflight is not a guard at all.
    """
    repo = _init_git_repo(tmp / f"wc-{case}")
    spec_dir, run_id = _code_implementation_run(repo, "demo")
    _receipt(repo, spec_dir, run_id, "T1", 0)
    before = (spec_dir / "engine-state.json").read_bytes()
    before_cohort = (spec_dir / "state.json").read_text(encoding="utf-8")

    wider_plan = (
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n\n"
        "### T3\n\n**Depends on:** T2\n"
    )
    new_run_id = str(uuid.uuid4())
    argvs = []
    for m in mutators:
        if m[0] == "reset":
            argvs.append(["reset", str(spec_dir)])
        elif m[0] == "init":
            argvs.append(["init", str(spec_dir), "--run-id", new_run_id])
        elif m[0] == "schedule":
            # Repartition for real. A re-run schedule over an unchanged plan
            # rewrites byte-identical content, which moves nothing and would
            # make this case vacuous.
            argvs.append(["__write_plan__", str(spec_dir / "plan.md"), wider_plan])
            expect = new_run_id if any(x[0] == "init" for x in mutators) else run_id
            argvs.append(["schedule", str(spec_dir), "--expect-run-id", expect])
        else:
            argvs.append([*m, str(spec_dir), "--expect-run-id", run_id])

    engine_res, mutator_res, probe = _run_interleaved(
        repo, ["transition", str(spec_dir), "wave-complete"], argvs
    )
    _assert_refused_without_writing(engine_res, mutator_res, probe, spec_dir,
                                    before, before_cohort)


def test_wave_complete_refuses_a_schedule_that_creates_the_receipts_container(
    tmp: Path,
) -> None:
    """AC11: the guard passed BECAUSE receipts were unenforced, then they were not.

    This is the case that killed the pinned-fields design: the absent-container
    row approves without reading the wave pointer or the partition at all, so a
    check over those two facts sees nothing move while `schedule` creates the
    container and leaves the current wave unaccounted.
    """
    repo = _init_git_repo(tmp / "wc-container")
    spec_dir, run_id = _code_implementation_run(repo, "demo")
    state = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))
    receipts_key = next(k for k in state if "receipt" in k.lower())
    del state[receipts_key]
    (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    before = (spec_dir / "engine-state.json").read_bytes()
    before_cohort = (spec_dir / "state.json").read_text(encoding="utf-8")

    engine_res, mutator_res, probe = _run_interleaved(
        repo,
        ["transition", str(spec_dir), "wave-complete"],
        [["schedule", str(spec_dir), "--expect-run-id", run_id]],
    )
    _assert_refused_without_writing(engine_res, mutator_res, probe, spec_dir,
                                    before, before_cohort)


def test_gates_clean_refuses_a_schedule_in_its_commit_window(tmp: Path) -> None:
    """AC11: the second serialised edge.

    Paired with `schedule`, not `wave advance`: `gates-clean` passes only on the
    final wave and `wave advance` refuses FROM the final wave, so no advance can
    ever commit in this window. A test written against `wave advance` here would
    be unsatisfiable by anything it claims to exercise.
    """
    repo = _init_git_repo(tmp / "gc-schedule")
    spec_dir, run_id = _code_implementation_run(repo, "demo", tasks="T1")
    _receipt(repo, spec_dir, run_id, "T1", 0)
    r = _run(ENGINE, "transition", str(spec_dir), "wave-complete", cwd=repo)
    assert r.returncode == 0, r.stderr
    before = (spec_dir / "engine-state.json").read_bytes()
    before_cohort = (spec_dir / "state.json").read_text(encoding="utf-8")
    wider_plan = (
        "# Plan\n\n- **Status:** Approved\n\n"
        "### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n"
    )

    engine_res, mutator_res, probe = _run_interleaved(
        repo,
        ["transition", str(spec_dir), "gates-clean"],
        [
            ["__write_plan__", str(spec_dir / "plan.md"), wider_plan],
            ["schedule", str(spec_dir), "--expect-run-id", run_id],
        ],
    )
    _assert_refused_without_writing(engine_res, mutator_res, probe, spec_dir,
                                    before, before_cohort)


def test_a_peer_holding_the_cohort_lock_blocks_the_commit(tmp: Path) -> None:
    """AC4: the lock's actual job, observed rather than inferred.

    Every interleaving case above forces the mutation to commit BEFORE the
    engine commits, so each would still pass with the cohort lock deleted or
    taken on a different path — the refusal there comes from the fingerprint
    alone. What the lock adds is excluding a mutation that would land BETWEEN
    the re-read and the state write, and only holding it from a peer can show
    that.

    Observed while the peer still holds it, not after: `_release` unlinks the
    lockfile on every normal exit, so a post-run probe reports the same absence
    whether the lock was taken or never taken at all.
    """
    repo = _init_git_repo(tmp / "mutual-exclusion")
    spec_dir, run_id = _code_implementation_run(repo, "demo")
    _receipt(repo, spec_dir, run_id, "T1", 0)
    before = (spec_dir / "engine-state.json").read_bytes()

    sl = _load_module(SCRIPT_DIR / "_statelock.py", "_statelock_mutual")
    state_path = spec_dir / "state.json"

    with sl.exclusive(state_path):
        child = subprocess.Popen(
            [sys.executable, str(ENGINE), "transition", str(spec_dir), "wave-complete"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", cwd=str(repo),
        )
        # Hold well past the point a lock-free implementation would have
        # committed, and keep checking rather than checking once at the end.
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            assert (spec_dir / "engine-state.json").read_bytes() == before, (
                "the transition committed while a peer held the cohort lock — "
                "the hold is absent, or taken on a path the cohort does not use"
            )
            time.sleep(0.05)
        assert child.poll() is None, (
            "the transition finished while the cohort lock was held; it never "
            "waited on the lock"
        )

    out, err = child.communicate(timeout=HARNESS_PROCESS_TIMEOUT)
    assert child.returncode == 0, f"it should proceed once released: {out}{err}"
    assert (spec_dir / "engine-state.json").read_bytes() != before
