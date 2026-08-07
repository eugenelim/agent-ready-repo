#!/usr/bin/env python3
"""Unit tests for _statelock.py — the work-loop's hardened state lock.

Run: python3 test-statelock.py
Exit 0 = all pass; exit non-zero = at least one failure.

Covers the port's hardening over agentbundle/statelock.py (ADR-0074): bounded
wait on every retry path, refusal of a non-regular lock path, ownership-checked
release, no mkdir, and a timeout exception that broad OSError handlers cannot
swallow.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import stat
import sys
import tempfile
import threading
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
    """Load _statelock.py. Red until T1 creates it."""
    spec = importlib.util.spec_from_file_location("_statelock", str(STATELOCK))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {STATELOCK}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── AC1 / AC2 — stdlib-only, one code path per platform ────────────────────

# STUB: AC1
def test_stdlib_only_via_ast(_tmp: Path) -> None:
    """Import nodes only, never a substring grep — the module's own prose
    explains why fcntl is unavailable, which a grep would trip on."""
    tree = ast.parse(STATELOCK.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    third_party = imported - set(sys.stdlib_module_names)
    if third_party:
        fail("stdlib-only", f"non-stdlib imports: {sorted(third_party)}")
        return
    ok("stdlib-only")


# STUB: AC2
def test_no_platform_locking_imports(_tmp: Path) -> None:
    tree = ast.parse(STATELOCK.read_text(encoding="utf-8"))
    banned = {"fcntl", "msvcrt"}
    hits: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits |= {a.name.split(".")[0] for a in node.names} & banned
        elif isinstance(node, ast.ImportFrom) and node.module:
            hits |= {node.module.split(".")[0]} & banned
    if hits:
        fail("no-platform-locking-imports", f"imported {sorted(hits)}")
        return
    ok("no-platform-locking-imports")


# ── AC3 — mutual exclusion, and no residue on either exit path ─────────────

# STUB: AC3
def test_mutual_exclusion(tmp: Path) -> None:
    mod = _load()
    target = tmp / "mx" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    overlaps = 0
    inside = 0
    guard = threading.Lock()

    def worker() -> None:
        nonlocal overlaps, inside
        with mod.exclusive(target, timeout=10.0):
            with guard:
                inside += 1
                if inside > 1:
                    overlaps += 1
            time.sleep(0.01)
            with guard:
                inside -= 1

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if overlaps:
        fail("mutual-exclusion", f"{overlaps} overlapping holders")
        return
    ok("mutual-exclusion")


# STUB: AC3
def test_no_lockfile_after_body_raises(tmp: Path) -> None:
    mod = _load()
    target = tmp / "raise" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    lock = target.with_name(target.name + ".lock")
    try:
        with mod.exclusive(target):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    if lock.exists():
        fail("no-lockfile-after-raise", f"{lock} survived an exception in the body")
        return
    ok("no-lockfile-after-raise")


# ── AC4 — mode 0600, pid recorded, timeout message is attributable ─────────

# STUB: AC4
def test_mode_0600_and_pid_recorded(tmp: Path) -> None:
    mod = _load()
    target = tmp / "mode" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    lock = target.with_name(target.name + ".lock")
    with mod.exclusive(target):
        mode = stat.S_IMODE(lock.stat().st_mode)
        body = lock.read_text(encoding="utf-8")
    if mode != 0o600:
        fail("lock-mode-0600", f"mode was {oct(mode)}")
        return
    if str(os.getpid()) not in body:
        fail("lock-mode-0600", f"holder pid not recorded in lockfile (got {body!r})")
        return
    ok("lock-mode-0600")


# STUB: AC4
def test_timeout_message_names_path_and_pid(tmp: Path) -> None:
    mod = _load()
    target = tmp / "msg" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    with mod.exclusive(target):
        try:
            with mod.exclusive(target, timeout=0.2):
                fail("timeout-message", "acquired a lock that was already held")
                return
        except mod.StateLockTimeout as exc:
            msg = str(exc)
    if ".lock" not in msg or str(os.getpid()) not in msg:
        fail("timeout-message", f"message names neither path nor holder pid: {msg!r}")
        return
    ok("timeout-message")


# ── AC5 — bounded wait: no hot spin on a non-regular lock path ─────────────

def _assert_terminates(mod, target: Path, name: str) -> None:
    """The precedent spins forever here at ~98% CPU (notes/reproduction.md C)."""
    t0 = time.monotonic()
    try:
        with mod.exclusive(target, timeout=0.5):
            fail(name, "acquired a lock whose path is not a regular file")
            return
    except mod.StateLockTimeout:
        pass
    except OSError:
        pass  # refusing loudly is also fail-closed
    elapsed = time.monotonic() - t0
    if elapsed > 5.0:
        fail(name, f"did not terminate promptly ({elapsed:.1f}s for timeout=0.5)")
        return
    ok(name)


# STUB: AC5
def test_dangling_symlink_terminates(tmp: Path) -> None:
    mod = _load()
    target = tmp / "sym" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    os.symlink(tmp / "sym" / "nope", target.with_name(target.name + ".lock"))
    _assert_terminates(mod, target, "dangling-symlink-terminates")


# STUB: AC5
def test_directory_at_lock_path_terminates(tmp: Path) -> None:
    mod = _load()
    target = tmp / "dir" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    target.with_name(target.name + ".lock").mkdir()
    _assert_terminates(mod, target, "directory-at-lock-path-terminates")


# STUB: AC5
def test_fifo_at_lock_path_terminates(tmp: Path) -> None:
    mod = _load()
    if not hasattr(os, "mkfifo"):
        ok("fifo-at-lock-path-terminates (skipped: no os.mkfifo)")
        return
    target = tmp / "fifo" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    os.mkfifo(target.with_name(target.name + ".lock"))
    _assert_terminates(mod, target, "fifo-at-lock-path-terminates")


# ── AC6 / AC7 — reclaim yields one holder; release is ownership-checked ────

# STUB: AC6
def test_concurrent_reclaimers_yield_one_holder(tmp: Path) -> None:
    """Invariant, not mechanism: the .reclaim.<pid> name is transient."""
    mod = _load()
    target = tmp / "reclaim" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("99999")
    os.utime(lock, (time.time() - 10_000, time.time() - 10_000))  # stale

    inside = 0
    overlaps = 0
    guard = threading.Lock()

    def worker() -> None:
        nonlocal inside, overlaps
        try:
            with mod.exclusive(target, timeout=10.0, stale_after=1.0):
                with guard:
                    inside += 1
                    if inside > 1:
                        overlaps += 1
                time.sleep(0.01)
                with guard:
                    inside -= 1
        except mod.StateLockTimeout:
            pass

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if overlaps:
        fail("concurrent-reclaimers", f"{overlaps} overlapping holders after reclaim")
        return
    ok("concurrent-reclaimers")


# STUB: AC7
def test_release_is_ownership_checked(tmp: Path) -> None:
    """A holder whose lock was reclaimed must not unlink its successor's."""
    mod = _load()
    target = tmp / "own" / "state.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}")
    lock = target.with_name(target.name + ".lock")
    with mod.exclusive(target):
        lock.write_text("someone-else's-token")  # simulate a reclaim + re-create
    if not lock.exists():
        fail("release-ownership-checked",
             "release unlinked a lockfile it no longer owned")
        return
    lock.unlink()
    ok("release-ownership-checked")


# ── AC8 — the timeout is not swallowable by a broad OSError handler ────────

# STUB: AC8
def test_timeout_is_not_oserror(_tmp: Path) -> None:
    mod = _load()
    if issubclass(mod.StateLockTimeout, OSError):
        fail("timeout-not-oserror",
             "StateLockTimeout derives from OSError; a broad except OSError "
             "in loop-cohort.py/loop-engine.py would swallow it")
        return
    ok("timeout-not-oserror")


# ── AC9 — taking the lock creates no directory ─────────────────────────────

# STUB: AC9
def test_no_mkdir(tmp: Path) -> None:
    mod = _load()
    missing = tmp / "nope" / "deeper" / "state.json"
    try:
        with mod.exclusive(missing, timeout=0.2):
            pass
    except Exception:
        pass
    if missing.parent.exists():
        fail("no-mkdir", f"lock acquisition created {missing.parent}")
        return
    ok("no-mkdir")


def main() -> int:
    tests = [
        test_stdlib_only_via_ast,
        test_no_platform_locking_imports,
        test_mutual_exclusion,
        test_no_lockfile_after_body_raises,
        test_mode_0600_and_pid_recorded,
        test_timeout_message_names_path_and_pid,
        test_dangling_symlink_terminates,
        test_directory_at_lock_path_terminates,
        test_fifo_at_lock_path_terminates,
        test_concurrent_reclaimers_yield_one_holder,
        test_release_is_ownership_checked,
        test_timeout_is_not_oserror,
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
