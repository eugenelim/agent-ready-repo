#!/usr/bin/env python3
"""Unit tests for _statelock.py — the work-loop's state lock.

Run: python3 test-statelock.py
Exit 0 = all pass; exit non-zero = at least one failure.

Subject is the PROJECTED copy under the skill's scripts/, not the package
source, so this suite also proves the projection is importable standalone —
stdlib-only, no agentbundle on sys.path (ADR-0074).

Covers the hardening over agentbundle/statelock.py: bounded wait on every retry
path, refusal of a non-regular lock path, inode-keyed ownership on release with
a loud report when the lock was lost, no mkdir, a validated lockfile record, and
an exception hierarchy that broad `except OSError` handlers cannot swallow.

Mutual exclusion and reclaim are driven with SEPARATE OS PROCESSES. Threads in
one interpreter cannot distinguish an O_EXCL lockfile from a process-local mutex,
which is the one property those cases exist to pin.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import stat
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
STATELOCK = SCRIPT_DIR / "_statelock.py"

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


def _load():
    spec = importlib.util.spec_from_file_location("_statelock", str(STATELOCK))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {STATELOCK}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _target(tmp: Path, name: str) -> Path:
    d = tmp / name
    d.mkdir(parents=True, exist_ok=True)
    t = d / "state.json"
    t.write_text("{}", encoding="utf-8")
    return t


# ── AC1 / AC2 — stdlib-only, no platform branch ────────────────────────────

# STUB: AC1
def test_imports_only_stdlib(_tmp: Path) -> None:
    """Import nodes, not a substring grep — the module's own docstring
    discusses fcntl, which a grep would trip on."""
    tree = ast.parse(STATELOCK.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    non_stdlib = imported - set(sys.stdlib_module_names)
    if non_stdlib:
        fail("imports-only-stdlib", f"non-stdlib imports: {sorted(non_stdlib)}")
        return
    if "agentbundle" in imported:
        fail("imports-only-stdlib", "the projected copy imports agentbundle")
        return
    ok("imports-only-stdlib")


# STUB: AC2
def test_no_platform_locking_imports(_tmp: Path) -> None:
    tree = ast.parse(STATELOCK.read_text(encoding="utf-8"))
    banned, hits = {"fcntl", "msvcrt"}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits |= {a.name.split(".")[0] for a in node.names} & banned
        elif isinstance(node, ast.ImportFrom) and node.module:
            hits |= {node.module.split(".")[0]} & banned
    if hits:
        fail("no-platform-locking-imports", f"imported {sorted(hits)}")
        return
    ok("no-platform-locking-imports")


# ── AC5 — mutual exclusion, ACROSS PROCESSES ───────────────────────────────

_MX_CHILD = '''
import importlib.util, os, sys, time
mod_path, target, log, go = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("_statelock", mod_path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
while not os.path.exists(go):
    pass
try:
    with m.exclusive(__import__("pathlib").Path(target), timeout=30.0):
        with open(log, "a") as fh:
            fh.write(f"ENTER {os.getpid()}\\n"); fh.flush()
        time.sleep(0.02)
        with open(log, "a") as fh:
            fh.write(f"EXIT {os.getpid()}\\n"); fh.flush()
except Exception as exc:
    with open(log, "a") as fh:
        fh.write(f"ERROR {type(exc).__name__}\\n")
    sys.exit(1)
'''


# STUB: AC5
def test_mutual_exclusion_across_processes(tmp: Path) -> None:
    target = _target(tmp, "mx")
    child = tmp / "_mx_child.py"
    child.write_text(_MX_CHILD, encoding="utf-8")
    log = tmp / "mx.log"
    log.write_text("", encoding="utf-8")
    go = tmp / "mx.go"

    procs = [
        subprocess.Popen(
            [sys.executable, str(child), str(STATELOCK), str(target),
             str(log), str(go)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for _ in range(6)
    ]
    time.sleep(0.5)  # let every child finish startup before releasing them
    go.write_text("go", encoding="utf-8")
    for p in procs:
        p.communicate(timeout=90)

    lines = [line.split() for line in log.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    if any(rec[0] == "ERROR" for rec in lines):
        fail("mutual-exclusion-across-processes", f"a child errored: {lines}")
        return
    if len(lines) != 12:
        fail("mutual-exclusion-across-processes",
             f"expected 6 ENTER/EXIT pairs, got {len(lines)} records")
        return
    # Strict alternation proves no two holders overlapped.
    depth = 0
    for kind, _pid in lines:
        depth += 1 if kind == "ENTER" else -1
        if depth > 1:
            fail("mutual-exclusion-across-processes",
                 f"two processes held the lock at once: {lines}")
            return
    ok("mutual-exclusion-across-processes")


# ── AC6 — no residue on either exit path ───────────────────────────────────

# STUB: AC6
def test_no_residue_on_return_and_on_raise(tmp: Path) -> None:
    mod = _load()
    for label, body_raises in (("return", False), ("raise", True)):
        target = _target(tmp, f"res-{label}")
        lock = target.with_name(target.name + ".lock")
        try:
            with mod.exclusive(target):
                if body_raises:
                    raise RuntimeError("boom")
        except RuntimeError:
            pass
        if lock.exists():
            fail("no-residue", f"lockfile survived the {label} path")
            return
    ok("no-residue")


# ── AC7 — one non-OSError base for every acquisition failure ───────────────

# STUB: AC7
def test_errors_are_not_oserror(_tmp: Path) -> None:
    mod = _load()
    classes = [mod.StateLockError, mod.StateLockTimeout,
               mod.StateLockUnusable, mod.StateLockLost]
    bad = [c.__name__ for c in classes if issubclass(c, OSError)]
    if bad:
        fail("errors-not-oserror",
             f"{bad} derive from OSError; a broad `except OSError` in "
             "loop-cohort.py/loop-engine.py would swallow them")
        return
    if not all(issubclass(c, mod.StateLockError) for c in classes[1:]):
        fail("errors-not-oserror", "not every lock error shares one base")
        return
    ok("errors-not-oserror")


# STUB: AC7
def test_unwritable_dir_fails_closed(tmp: Path) -> None:
    """EACCES must arrive as a StateLockError, not a raw OSError traceback."""
    mod = _load()
    if os.name != "posix" or os.geteuid() == 0:
        ok("unwritable-dir-fails-closed (skipped: needs non-root POSIX)")
        return
    target = _target(tmp, "eacces")
    Path(target.parent).chmod(0o500)
    try:
        with mod.exclusive(target, timeout=0.2):
            fail("unwritable-dir-fails-closed", "acquired a lock in a read-only dir")
            return
    except mod.StateLockError:
        pass
    except OSError as exc:
        fail("unwritable-dir-fails-closed",
             f"raw {type(exc).__name__} escaped instead of StateLockError")
        return
    finally:
        Path(target.parent).chmod(0o700)
    ok("unwritable-dir-fails-closed")


# ── AC8 — bounded wait, no hot spin ────────────────────────────────────────

def _assert_unacquirable_fast(mod, target: Path, name: str) -> None:
    """The precedent spins here at ~98% CPU forever (notes/reproduction.md C).

    Two assertions, both needed: it must fail in LESS than the timeout (it is
    unacquirable, not contended — waiting cannot help), and it must burn no
    measurable CPU (a deadline-respecting spin would satisfy the first alone).
    """
    timeout = 1.0
    t0, c0 = time.monotonic(), time.process_time()
    try:
        with mod.exclusive(target, timeout=timeout):
            fail(name, "acquired a lock whose path is not a regular file")
            return
    except mod.StateLockUnusable as exc:
        if ".lock" not in str(exc):
            fail(name, f"refusal does not name the lock path: {str(exc)[:80]!r}")
            return
    except mod.StateLockError as exc:
        fail(name, f"expected StateLockUnusable, got {type(exc).__name__}")
        return
    wall, cpu = time.monotonic() - t0, time.process_time() - c0
    if wall >= timeout:
        fail(name, f"waited {wall:.2f}s for an unacquirable path (timeout {timeout}s) "
                   "— it should refuse at once, not wait out the deadline")
        return
    if cpu > wall / 2 and cpu > 0.05:
        fail(name, f"burned {cpu:.2f}s CPU over {wall:.2f}s wall — that is a spin")
        return
    ok(name)


# STUB: AC8
def test_dangling_symlink_refused_fast(tmp: Path) -> None:
    mod = _load()
    target = _target(tmp, "sym")
    Path(target.with_name(target.name + ".lock")).symlink_to(tmp / "sym" / "nope")
    _assert_unacquirable_fast(mod, target, "dangling-symlink-refused-fast")


# STUB: AC8
def test_directory_refused_fast(tmp: Path) -> None:
    mod = _load()
    target = _target(tmp, "dir")
    target.with_name(target.name + ".lock").mkdir()
    _assert_unacquirable_fast(mod, target, "directory-refused-fast")


# STUB: AC8
def test_fifo_refused_fast(tmp: Path) -> None:
    mod = _load()
    if not hasattr(os, "mkfifo"):
        ok("fifo-refused-fast (skipped: no os.mkfifo)")
        return
    target = _target(tmp, "fifo")
    os.mkfifo(target.with_name(target.name + ".lock"))
    _assert_unacquirable_fast(mod, target, "fifo-refused-fast")


# STUB: AC8
def test_contention_sleeps_rather_than_spins(tmp: Path) -> None:
    mod = _load()
    target = _target(tmp, "spin")
    with mod.exclusive(target):
        t0, c0 = time.monotonic(), time.process_time()
        try:
            with mod.exclusive(target, timeout=0.5):
                fail("contention-sleeps", "acquired a held lock")
                return
        except mod.StateLockTimeout:
            pass
        wall, cpu = time.monotonic() - t0, time.process_time() - c0
    if cpu > wall / 2:
        fail("contention-sleeps", f"burned {cpu:.2f}s CPU over {wall:.2f}s waiting")
        return
    ok("contention-sleeps")


# ── AC9 — reclaim and release cannot admit or mask a second writer ─────────

_RECLAIM_CHILD = '''
import importlib.util, os, sys
mod_path, target, log, go = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("_statelock", mod_path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
while not os.path.exists(go):
    pass
try:
    with m.exclusive(__import__("pathlib").Path(target), timeout=20.0, stale_after=1.0):
        with open(log, "a") as fh:
            fh.write(f"ENTER {os.getpid()}\\n"); fh.flush()
        import time; time.sleep(0.02)
        with open(log, "a") as fh:
            fh.write(f"EXIT {os.getpid()}\\n"); fh.flush()
except Exception as exc:
    with open(log, "a") as fh:
        fh.write(f"ERR {type(exc).__name__}\\n")
'''


# STUB: AC9
def test_concurrent_reclaimers_yield_one_holder(tmp: Path) -> None:
    """Invariant, not mechanism — the .reclaim.<uuid> name is transient."""
    target = _target(tmp, "reclaim")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("statelock1 " + "a" * 32 + " 99999\n", encoding="utf-8")
    old = time.time() - 10_000
    os.utime(lock, (old, old))

    child = tmp / "_reclaim_child.py"
    child.write_text(_RECLAIM_CHILD, encoding="utf-8")
    log = tmp / "reclaim.log"
    log.write_text("", encoding="utf-8")
    go = tmp / "reclaim.go"
    procs = [
        subprocess.Popen(
            [sys.executable, str(child), str(STATELOCK), str(target),
             str(log), str(go)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for _ in range(5)
    ]
    time.sleep(0.5)
    go.write_text("go", encoding="utf-8")
    for p in procs:
        p.communicate(timeout=90)

    lines = [line.split() for line in log.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    depth = 0
    for rec in lines:
        if rec[0] == "ENTER":
            depth += 1
        elif rec[0] == "EXIT":
            depth -= 1
        if depth > 1:
            fail("concurrent-reclaimers-one-holder",
                 f"two holders after a reclaim race: {lines}")
            return
    if not any(rec[0] == "ENTER" for rec in lines):
        fail("concurrent-reclaimers-one-holder",
             f"nobody reclaimed the stale lock: {lines}")
        return
    ok("concurrent-reclaimers-one-holder")


# STUB: AC9
def test_reclaim_refuses_unrecognised_file(tmp: Path) -> None:
    """An ancient file that is not our record must not be deleted."""
    mod = _load()
    target = _target(tmp, "foreign")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("somebody else's file\n", encoding="utf-8")
    old = time.time() - 10_000
    os.utime(lock, (old, old))
    try:
        with mod.exclusive(target, timeout=0.3, stale_after=1.0):
            fail("reclaim-refuses-unrecognised", "deleted a foreign file and acquired")
            return
    except mod.StateLockTimeout:
        pass
    if not lock.exists():
        fail("reclaim-refuses-unrecognised", "the foreign file was deleted")
        return
    if lock.read_text(encoding="utf-8") != "somebody else's file\n":
        fail("reclaim-refuses-unrecognised", "the foreign file was modified")
        return
    ok("reclaim-refuses-unrecognised")


# STUB: AC9
def test_lost_lock_is_reported(tmp: Path) -> None:
    """The deep one: a reclaimed holder must NOT complete quietly.

    Simulated as a real reclaim — the lockfile is renamed away and a fresh one
    put in its place, so a correct inode-keyed release sees a foreign file.
    """
    mod = _load()
    target = _target(tmp, "lost")
    lock = target.with_name(target.name + ".lock")
    successor = "statelock1 " + "f" * 32 + " 4242\n"
    try:
        with mod.exclusive(target):
            Path(lock).rename(lock.with_name(lock.name + ".stolen"))
            lock.write_text(successor, encoding="utf-8")
    except mod.StateLockLost as exc:
        if "state.json" not in str(exc):
            fail("lost-lock-reported", f"report does not name the state file: {exc}")
            return
        if lock.read_text(encoding="utf-8") != successor:
            fail("lost-lock-reported", "release deleted the successor's lockfile")
            return
        ok("lost-lock-reported")
        return
    fail("lost-lock-reported",
         "a holder whose lock was reclaimed mid-body returned without raising — "
         "it would exit 0 having possibly lost its write")


# ── AC11 — record, mode, attributability ───────────────────────────────────

# STUB: AC11
def test_lockfile_mode_and_record(tmp: Path) -> None:
    mod = _load()
    target = _target(tmp, "rec")
    lock = target.with_name(target.name + ".lock")
    with mod.exclusive(target):
        mode = stat.S_IMODE(lock.stat().st_mode)
        body = lock.read_text(encoding="utf-8")
    if mode != 0o600:
        fail("lockfile-mode-and-record", f"mode was {oct(mode)}, want 0o600")
        return
    parts = body.split()
    if len(parts) != 3 or parts[0] != "statelock1" or parts[2] != str(os.getpid()):
        fail("lockfile-mode-and-record", f"malformed record {body!r}")
        return
    if len(body.encode()) > 256:
        fail("lockfile-mode-and-record", "record exceeds the 256-byte bound")
        return
    ok("lockfile-mode-and-record")


# STUB: AC11
def test_timeout_names_the_recorded_holder(tmp: Path) -> None:
    """Plant a DISTINCTIVE foreign pid: asserting on os.getpid() would pass for
    an implementation that formats its own pid, which is not attributability."""
    mod = _load()
    target = _target(tmp, "attrib")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("statelock1 " + "b" * 32 + " 1234567\n", encoding="utf-8")
    try:
        with mod.exclusive(target, timeout=0.2):
            fail("timeout-names-holder", "acquired a held lock")
            return
    except mod.StateLockTimeout as exc:
        msg = str(exc)
    if "1234567" not in msg:
        fail("timeout-names-holder", f"message omits the recorded pid: {msg!r}")
        return
    if ".lock" not in msg:
        fail("timeout-names-holder", f"message omits the lock path: {msg!r}")
        return
    ok("timeout-names-holder")


# STUB: AC11
def test_unparseable_pid_is_not_rendered(tmp: Path) -> None:
    """Lockfile bytes must never reach a message unvalidated (CWE-117)."""
    mod = _load()
    target = _target(tmp, "inject")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("statelock1 " + "c" * 32 + " \x1b[31mBOOM\n", encoding="utf-8")
    try:
        with mod.exclusive(target, timeout=0.2):
            fail("unparseable-pid-not-rendered", "acquired a held lock")
            return
    except mod.StateLockTimeout as exc:
        msg = str(exc)
    if "BOOM" in msg or "\x1b" in msg:
        fail("unparseable-pid-not-rendered",
             f"unvalidated lockfile bytes reached the message: {msg!r}")
        return
    ok("unparseable-pid-not-rendered")


# ── AC12 — no mkdir ────────────────────────────────────────────────────────

# STUB: AC12
def test_no_mkdir(tmp: Path) -> None:
    mod = _load()
    missing = tmp / "absent" / "deeper" / "state.json"
    try:
        with mod.exclusive(missing, timeout=0.2):
            pass
    except (mod.StateLockError, OSError):
        pass
    if missing.parent.exists():
        fail("no-mkdir", f"lock acquisition created {missing.parent}")
        return
    ok("no-mkdir")


def main() -> int:
    tests = [
        test_imports_only_stdlib,
        test_no_platform_locking_imports,
        test_mutual_exclusion_across_processes,
        test_no_residue_on_return_and_on_raise,
        test_errors_are_not_oserror,
        test_unwritable_dir_fails_closed,
        test_dangling_symlink_refused_fast,
        test_directory_refused_fast,
        test_fifo_refused_fast,
        test_contention_sleeps_rather_than_spins,
        test_concurrent_reclaimers_yield_one_holder,
        test_reclaim_refuses_unrecognised_file,
        test_lost_lock_is_reported,
        test_lockfile_mode_and_record,
        test_timeout_names_the_recorded_holder,
        test_unparseable_pid_is_not_rendered,
        test_no_mkdir,
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
