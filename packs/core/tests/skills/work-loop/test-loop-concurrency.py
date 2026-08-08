#!/usr/bin/env python3
"""Concurrency regressions for loop-cohort.py and loop-engine.py.

Run: python3 test-loop-concurrency.py
Exit 0 = all pass; exit non-zero = at least one failure.

These are the acceptance bar for docs/specs/loop-cohort-state-lock. Both cases
were observed failing against the pre-fix tree — see notes/reproduction.md.

THE HARNESS IS THE POINT. The synchronising barrier sits AFTER interpreter and
module startup: each child loads the target module, spins to a shared wall-clock
instant, then calls main(argv). Without that, ~40 ms of Python startup per
process smears the children apart and the microsecond-wide critical section is
never entered concurrently — a naive fan-out of 20 subprocesses loses nothing in
5 of 5 trials and would pass against the unfixed tree.

Separate OS processes, never threads: threads share os.chdir, the module-level
_lint_module global, and sys.stdout, so they neither exercise the cross-process
contract the lock exists for nor permit sound per-caller exit-code assertions.

Hermetic: every case runs against a throwaway git repo so loop-engine's
_get_repo_root() resolves inside tmp_path. The live repo's .loop-run/ and
.gitignore must not be touched — this suite would otherwise replay or discard
the pending event of the very run that owns this PR.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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

# The barriered child, in two phases. A *guessed* lead is what smears children
# apart on a loaded runner — measured at 495 ms and 3756 ms of spread with a 1 s
# lead, which silently destroys the suite's discriminating power. So the child
# announces readiness only after its startup is paid, then rendezvouses on a go
# file the parent creates once every child is ready. It records its own
# post-barrier instant so the parent can prove they actually raced.
_CHILD_SRC = '''
import importlib.util, os, sys, time
ready_file = sys.argv[1]; go_file = sys.argv[2]; arrival_file = sys.argv[3]
target = sys.argv[4]; argv = sys.argv[5:]
spec = importlib.util.spec_from_file_location("_subject", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)          # startup paid BEFORE announcing ready
open(ready_file, "w").write("1")      # phase 1: announce
while not os.path.exists(go_file):    # phase 2: rendezvous on the parent's go
    time.sleep(0.0002)                # ~0.2ms: 250x tighter than the spread cap
open(arrival_file, "w").write(repr(time.time()))
sys.exit(mod.main(argv))
'''

# Max spread between children's post-barrier instants. The critical sections
# being raced are microseconds wide, so arrivals must cluster far tighter than
# the ~40 ms of startup the barrier exists to absorb.
MAX_ARRIVAL_SPREAD = 0.050

# The live repo this suite must not touch. parents[5], not [4]: [3] is
# packs/core, [4] is packs/, [5] is the repo root — getting that wrong made the
# hermeticity case pass vacuously.
LIVE_ROOT = Path(__file__).resolve().parents[5]


def _live_fingerprint() -> dict[str, str]:
    """{relpath: sha256} over the live .loop-run/ contents plus .gitignore.

    CONTENTS, not names: `loop-engine` APPENDS to events.jsonl and to
    .gitignore, so a name-only listing stays green through exactly the pollution
    this guards. Taken at IMPORT — a baseline captured inside the last test bakes
    in whatever the earlier cases already did.
    """
    import hashlib

    out: dict[str, str] = {}
    for target in (LIVE_ROOT / ".loop-run", LIVE_ROOT / ".gitignore"):
        if target.is_file():
            out[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        elif target.is_dir():
            for f in sorted(target.rglob("*")):
                if f.is_file():
                    out[str(f.relative_to(LIVE_ROOT))] = hashlib.sha256(
                        f.read_bytes()
                    ).hexdigest()
    return out


_LIVE_BASELINE = _live_fingerprint()

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


# ── hermetic fixture helpers (shape borrowed from
#    test_loop_engine_events_jsonl.py so _get_repo_root() lands in tmp_path) ──

def _child_path(root: Path) -> Path:
    p = root / "_barriered_child.py"
    if not p.exists():
        p.write_text(_CHILD_SRC, encoding="utf-8")
    return p


def _init_git_repo(path: Path) -> Path:
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    for cmd in (["git", "config", "user.email", "test@example.com"],
                ["git", "config", "user.name", "Test"]):
        subprocess.run(cmd, check=True, capture_output=True, cwd=str(path))
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
                          cwd=str(cwd))


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
    """Launch n children that all enter the critical section together.

    argvs is one argv per child. Returns [(rc, stdout, stderr)] per child —
    read from that child, never from a shared stream.
    """
    child = _child_path(cwd)
    arrivals_dir = cwd / "_arrivals"
    arrivals_dir.mkdir(exist_ok=True)
    for stale in arrivals_dir.iterdir():
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
             str(go_file), str(arrivals_dir / f"{i}.txt"), str(target), *argvs[i]],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", cwd=str(cwd),
        )
        for i in range(n)
    ]
    # Phase 1: wait for every child to finish interpreter + module startup.
    deadline = time.monotonic() + READY_TIMEOUT
    while len(list(ready_dir.iterdir())) < n and time.monotonic() < deadline:
        time.sleep(0.005)
    # Phase 2: release them all at once.
    go_file.write_text("go")

    results = []
    for p in procs:
        so, se = p.communicate()
        results.append((p.returncode, so, se))

    arrivals = []
    for f in sorted(arrivals_dir.iterdir()):
        with contextlib.suppress(OSError, ValueError):
            arrivals.append(float(f.read_text(encoding="ascii").strip()))
    spread = (max(arrivals) - min(arrivals)) if len(arrivals) > 1 else 0.0
    return results, spread, len(arrivals)


# STUB: AC20
def _check_barrier(name: str, n: int, spread: float, arrived: int) -> bool:
    """Every case must prove its children raced. A smeared run is a loud
    failure, not a quiet pass."""
    if arrived != n:
        fail(name, f"only {arrived}/{n} children recorded a post-barrier arrival")
        return False
    if spread > MAX_ARRIVAL_SPREAD:
        fail(name,
             f"children arrived {spread * 1000:.0f} ms apart (limit "
             f"{MAX_ARRIVAL_SPREAD * 1000:.0f} ms) — they did not race, so a pass "
             "here would prove nothing")
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
            res, spread, arrived = _run_barriered(n, COHORT, argvs, repo)
            if not _check_barrier("record-attempt-no-lost-update", n, spread, arrived):
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
        res, spread, arrived = _run_barriered(2, ENGINE, argvs, repo)
        if not _check_barrier("concurrent-identical-transition", 2, spread, arrived):
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
    res, spread, arrived = _run_barriered(n, COHORT, argvs, repo)
    if not _check_barrier("concurrent-init", n, spread, arrived):
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

# STUB: AC10
def test_lock_hold_budget(_tmp: Path) -> None:
    """timeout < max hold < stale_after, and every under-lock call is bounded.

    loop-engine holds the state lock across git-shelling guards. An unbounded
    call makes the max hold unprovable; if the real hold can exceed stale_after,
    a merely-slow holder is judged dead, its lock is reclaimed, and a second
    writer is admitted — reinstating the lost update. Adding a guard must not be
    able to break that quietly, so the bound is derived from the source here.
    """
    import ast as _ast

    src = ENGINE.read_text(encoding="utf-8")
    tree = _ast.parse(src)

    unbounded = []
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        fn = node.func
        if not (
            isinstance(fn, _ast.Attribute)
            and isinstance(fn.value, _ast.Name)
            and fn.value.id == "subprocess"
            and fn.attr in ("run", "Popen", "check_output")
        ):
            continue
        name = f"subprocess.{fn.attr}"
        if not any(kw.arg == "timeout" for kw in node.keywords):
            unbounded.append(f"{name} at {ENGINE.name}:{node.lineno}")
    if unbounded:
        fail("lock-hold-budget",
             "subprocess call(s) with no timeout= reachable while the lock is "
             f"held: {unbounded}. An unbounded call makes the maximum hold "
             "unprovable against stale_after.")
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
    ok("lock-hold-budget")


# ── AC18 — the suite does not touch the live repo ──────────────────────────

# STUB: AC21
def test_harness_is_hermetic(tmp: Path) -> None:
    """The live repo is byte-identical after a full run.

    Compared against the import-time baseline, so this covers what EVERY case
    above did, not just this one.
    """
    if not (LIVE_ROOT / ".git").exists():
        fail("harness-is-hermetic",
             f"{LIVE_ROOT} is not the repo root — check the parents[] depth")
        return

    # Exercise the engine once more for good measure, in its own temp repo.
    root = tmp / "herm"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    _engine_init(repo, spec_dir)
    _run_barriered(2, ENGINE, [["transition", str(spec_dir), "spec-ready"]] * 2, repo)

    if not (repo / ".loop-run").is_dir():
        fail("harness-is-hermetic",
             "the tmp repo has no .loop-run/ — the child did not resolve its "
             "repo root inside tmp_path, so the run was not hermetic")
        return

    now = _live_fingerprint()
    if now != _LIVE_BASELINE:
        changed = sorted(
            set(now) ^ set(_LIVE_BASELINE)
            | {k for k in set(now) & set(_LIVE_BASELINE) if now[k] != _LIVE_BASELINE[k]}
        )
        fail("harness-is-hermetic",
             f"the live repo changed during this suite: {changed}")
        return
    ok("harness-is-hermetic")


def main() -> int:
    tests = [
        test_concurrent_record_attempt_no_lost_update,
        test_concurrent_identical_transition,
        test_concurrent_init,
        test_locked_verbs_refuse_when_held,
        test_noop_paths_do_not_write,
        test_lock_hold_budget,
        test_harness_is_hermetic,
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for t in tests:
            try:
                t(tmp)
            except Exception as exc:
                fail(t.__name__, f"uncaught exception: {type(exc).__name__}: {exc}")

    print(f"\n{ran - len(failures)}/{ran} passed", end="")
    if failures:
        print(f"  FAILED: {', '.join(failures)}", file=sys.stderr)
        return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
