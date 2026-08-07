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
    pass
open(arrival_file, "w").write(repr(time.time()))
sys.exit(mod.main(argv))
'''

# Max spread between children's post-barrier instants. The critical sections
# being raced are microseconds wide, so arrivals must cluster far tighter than
# the ~40 ms of startup the barrier exists to absorb.
MAX_ARRIVAL_SPREAD = 0.050

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
        try:
            arrivals.append(float(f.read_text(encoding="ascii").strip()))
        except (OSError, ValueError):
            pass
    spread = (max(arrivals) - min(arrivals)) if len(arrivals) > 1 else 0.0
    return results, spread, len(arrivals)


def _check_barrier(name: str, n: int, spread: float, arrived: int) -> bool:
    """Every case must prove its children raced. A smeared run is a loud
    failure, not a quiet pass."""
    if arrived != n:
        fail(name, f"only {arrived}/{n} children recorded a post-barrier arrival")
        return False
    if spread > MAX_ARRIVAL_SPREAD:
        fail(name,
             f"children arrived {spread*1000:.0f} ms apart (limit "
             f"{MAX_ARRIVAL_SPREAD*1000:.0f} ms) — they did not race, so a pass "
             "here would prove nothing")
        return False
    return True


# ── AC15 — cohort: no lost update ──────────────────────────────────────────

# STUB: AC15
def test_concurrent_record_attempt_no_lost_update(tmp: Path) -> None:
    """Pre-fix: 20/20 trials lost an update at N=2 (notes/reproduction.md A)."""
    for n, trials in ((2, 20), (8, 5)):
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

# STUB: AC16
def test_concurrent_identical_transition(tmp: Path) -> None:
    """Pre-fix: 10/10 trials admitted BOTH (notes/reproduction.md B)."""
    for trial in range(10):
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
        rows = [json.loads(l) for l in
                events_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        keys = [(r.get("spec"), r.get("seq")) for r in rows]
        if len(keys) != len(set(keys)):
            fail("concurrent-identical-transition",
                 f"trial={trial}: duplicate (spec, seq) in the audit outbox: {keys}")
            return
    ok("concurrent-identical-transition")


# ── AC17 — init is not racy ────────────────────────────────────────────────

# STUB: AC17
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
                 f"a loser refused for the wrong reason (rc={rc}): {(so+se).strip()!r}")
            return
    ok("concurrent-init")


# ── AC13 — every locked verb refuses when the lock is held, and does not write ──

# STUB: AC13
def test_locked_verbs_refuse_when_held(tmp: Path) -> None:
    """Wiring, not the module: a module-level timeout test does not cover this.

    Filled in at T3/T4 — needs the lock module to expose a way for the test to
    hold the lock out-of-process. Asserts, per verb: non-zero exit AND a
    byte-identical state file.
    """
    fail("locked-verbs-refuse-when-held", "not implemented yet (T3/T4)")


# ── AC14 — locked no-op paths still do not write ───────────────────────────

# STUB: AC14
def test_noop_paths_do_not_write(tmp: Path) -> None:
    """record-attempt with a repeated --cycle-id, and approve-plan when already
    approved, must leave state.json's digest unchanged. Note: the existing
    test-loop-cohort.sh:426-436 case covers the unlocked read-only `status`
    verb and does NOT cover this."""
    fail("noop-paths-do-not-write", "not implemented yet (T3)")


# ── AC18 — the suite does not touch the live repo ──────────────────────────

# STUB: AC18
def test_harness_is_hermetic(tmp: Path) -> None:
    """Every case above passes cwd=<tmp repo>, so loop-engine's _get_repo_root()
    resolves inside tmp_path. Assert the real repo is untouched."""
    # parents[5], not [4]: [3] is packs/core, [4] is packs/, [5] is the repo
    # root. Getting this wrong made this case pass vacuously (no packs/.loop-run
    # exists, so before == after == None) — a false green in the one test whose
    # job is to catch false greens. The .git assertion makes a future move loud.
    live_root = Path(__file__).resolve().parents[5]
    if not (live_root / ".git").exists():
        fail("harness-is-hermetic",
             f"{live_root} is not the repo root — check the parents[] depth")
        return
    live_loop_run = live_root / ".loop-run"
    before = sorted(p.name for p in live_loop_run.iterdir()) if live_loop_run.is_dir() else None
    root = tmp / "herm"
    root.mkdir(parents=True)
    repo = _init_git_repo(root)
    spec_dir = _make_spec_dir(repo, "demo")
    _engine_init(repo, spec_dir)
    _run_barriered(2, ENGINE, [["transition", str(spec_dir), "spec-ready"]] * 2, repo)  # noqa
    after = sorted(p.name for p in live_loop_run.iterdir()) if live_loop_run.is_dir() else None
    if before != after:
        fail("harness-is-hermetic",
             f"the live repo's .loop-run/ changed: {before} -> {after}")
        return
    if not (repo / ".loop-run").is_dir():
        fail("harness-is-hermetic",
             "the tmp repo has no .loop-run/ — the child did not resolve its "
             "repo root inside tmp_path, so the run was not hermetic")
        return
    ok("harness-is-hermetic")


def main() -> int:
    tests = [
        test_concurrent_record_attempt_no_lost_update,
        test_concurrent_identical_transition,
        test_concurrent_init,
        test_locked_verbs_refuse_when_held,
        test_noop_paths_do_not_write,
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
