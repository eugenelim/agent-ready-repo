"""T1 (sso-store-transition-serialization): the per-profile lock primitive.

Covers the primitive standalone — path confinement, directory and file modes,
the bounded non-blocking acquire, the errno-based contention/fault split, the
``(thread, profile)``-keyed held-set, and the release path. Nothing here wires
the lock into a verb; that starts at T2.

Exception *types* are asserted here. The exit codes they map to are asserted in
T5, which adds the ``main`` handlers — the split is what keeps T1 buildable in
its own wave.
"""

from __future__ import annotations

import errno
import importlib.util
import os
import pathlib
import stat
import sys
import threading
import time
import types

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BROKER_PY = (
    REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
    / "sso-broker.py"
)

# `errno.EDEADLOCK` does not exist on macOS — BSD headers omit it, glibc aliases
# it to EDEADLK, MSVC defines it. Referencing it directly is an AttributeError on
# the platform this task's Done-when requires.
_EDEADLK = getattr(errno, "EDEADLOCK", errno.EDEADLK)

# `errno.EOPNOTSUPP` and `errno.ENOSYS` are POSIX-only names that not every
# platform's C library exposes. Guard with getattr to mirror the production
# code's `_LOCK_UNSUPPORTED_ERRNOS` frozenset — a direct attribute access in the
# @pytest.mark.parametrize list is evaluated at collection time, so an
# AttributeError here fails the *entire module*, not just the three test cases.
_LOCK_UNSUPPORTED_CODES: list[int] = [
    c
    for c in (
        getattr(errno, "ENOLCK", None),
        getattr(errno, "EOPNOTSUPP", None),
        getattr(errno, "ENOSYS", None),
    )
    if c is not None
]
# `ENOLCK` (39) is defined on every supported platform, so this list is never
# empty in practice. If it were empty, pytest would emit a collection warning
# and the test would not run — not an error. The guard still prevents a
# collection-time AttributeError on hypothetical platforms where all three
# names are absent.


def _load_broker(py_path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(py_path.parent))
    return mod


@pytest.fixture
def broker(tmp_path, monkeypatch):
    """The broker with its user-scope roots redirected under a sandboxed HOME."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    mod = _load_broker(BROKER_PY)
    mod._AGENTBUNDLE_HOME = home / ".agentbundle"
    mod._SSO_PROFILE_DIR = mod._AGENTBUNDLE_HOME / "sso-profiles"
    mod._SSO_COOKIE_FILE_FLOOR = mod._AGENTBUNDLE_HOME / "sso-cookies"
    mod._SSO_LOCK_DIR = mod._AGENTBUNDLE_HOME / "sso-locks"
    return mod


# ----------------------------------------------------------------------
# AC18 / AC19 — confinement and modes.
# ----------------------------------------------------------------------


def test_lock_path_refuses_traversal_before_opening_the_lockfile(broker):
    """AC18: a traversal-shaped profile raises before any file is opened."""
    with pytest.raises(broker.ProfileConfinementError):
        broker._sso_lock_path("../etc/passwd")
    assert not broker._SSO_LOCK_DIR.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits")
def test_lock_dir_is_0700_and_lockfile_is_0600(broker):
    """AC19: directory 0700, lockfile 0600, on first acquisition."""
    with broker._profile_lock("jira"):
        pass
    assert stat.S_IMODE(broker._SSO_LOCK_DIR.stat().st_mode) == 0o700
    assert stat.S_IMODE(broker._sso_lock_path("jira").stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits")
def test_pre_existing_0755_lock_dir_is_narrowed_on_next_acquisition(broker):
    """AC19: `mkdir(mode=...)` does not repair an existing directory.

    A 0755 lock directory lists every SSO profile the user holds to any local
    reader, so the repair is not cosmetic.
    """
    broker._SSO_LOCK_DIR.mkdir(parents=True, mode=0o755)
    broker._SSO_LOCK_DIR.chmod(0o755)  # defeat umask
    with broker._profile_lock("jira"):
        pass
    assert stat.S_IMODE(broker._SSO_LOCK_DIR.stat().st_mode) == 0o700


# ----------------------------------------------------------------------
# AC9 — the wait is bounded and the bound is honoured.
# ----------------------------------------------------------------------


def test_contended_acquire_raises_after_the_budget(broker):
    """AC9: a held lock yields StoreContendedError no sooner than the budget."""
    holding = threading.Event()
    release = threading.Event()

    def hold():
        with broker._profile_lock("jira"):
            holding.set()
            release.wait(10)

    t = threading.Thread(target=hold, daemon=True)
    t.start()
    assert holding.wait(5), "helper thread never acquired"
    try:
        started = time.monotonic()
        with pytest.raises(broker.StoreContendedError), broker._profile_lock("jira", budget_s=0.5):
            pass
        elapsed = time.monotonic() - started
        assert elapsed >= 0.5, f"gave up before the budget ({elapsed:.3f}s)"
        # Tight enough to catch an inverted clamp in the backoff loop; a 5 s
        # ceiling against a 0.5 s budget tolerated a 10x overshoot.
        assert elapsed < 0.5 + 0.5, f"overran the budget ({elapsed:.3f}s)"
    finally:
        release.set()
        t.join(5)


# ----------------------------------------------------------------------
# AC12 / AC13 — classification reads exc.errno and the raising call.
# ----------------------------------------------------------------------


@pytest.mark.skipif(os.name != "posix", reason="fcntl is POSIX-only")
def test_blocking_io_error_is_contention_not_fault(broker, monkeypatch):
    """AC12: the `BlockingIOError`-subclasses-`OSError` regression test.

    A classifier that catches `OSError` around the acquire swallows POSIX
    contention entirely and makes the contended path unreachable.
    """
    import fcntl

    assert issubclass(BlockingIOError, OSError)  # the trap, stated

    def refuse(fd, op):
        raise BlockingIOError(errno.EAGAIN, "resource temporarily unavailable")

    monkeypatch.setattr(fcntl, "flock", refuse)
    with pytest.raises(broker.StoreContendedError), broker._profile_lock("jira", budget_s=0.1):
        pass


@pytest.mark.parametrize(
    "exc",
    [
        PermissionError(errno.EACCES, "locking violation"),
        OSError(_EDEADLK, "locking violation"),
    ],
    ids=["EACCES", "EDEADLK"],
)
def test_windows_shaped_lock_refusals_are_contention(broker, monkeypatch, exc):
    """AC12: Windows signals contention through errno, not a distinct class.

    Two-argument form deliberately: `OSError(13).errno` is `None`, so a
    single-argument stub routes a *correct* classifier to the fault branch.
    """
    assert exc.errno is not None, "single-argument OSError carries no errno"
    monkeypatch.setattr(broker, "_acquire_once", lambda fd: (_ for _ in ()).throw(exc))
    with pytest.raises(broker.StoreContendedError), broker._profile_lock("jira", budget_s=0.1):
        pass


def test_same_errno_from_os_open_is_a_fault_not_contention(broker, monkeypatch):
    """AC13: the raising *call* decides, because EACCES is ambiguous by errno."""
    real_open = os.open

    def refuse(path, flags, mode=0o777):
        if str(path).endswith(".lock"):
            raise PermissionError(errno.EACCES, "permission denied")
        return real_open(path, flags, mode)

    monkeypatch.setattr(os, "open", refuse)
    with pytest.raises(broker.LockUnavailableError), broker._profile_lock("jira", budget_s=0.1):
        pass


@pytest.mark.parametrize("code", _LOCK_UNSUPPORTED_CODES, ids=str)
def test_filesystem_refusing_locks_is_a_fault(broker, monkeypatch, code):
    """AC13: a filesystem that cannot lock fails loudly, never silently.

    All three errnos AC13 names, two-argument so classification happens by
    `exc.errno` rather than by falling through to the fault default.
    """
    exc = OSError(code, os.strerror(code))
    assert exc.errno == code
    monkeypatch.setattr(broker, "_acquire_once", lambda fd: (_ for _ in ()).throw(exc))
    with pytest.raises(broker.LockUnavailableError), broker._profile_lock("jira", budget_s=0.1):
        pass


def test_symlink_loop_runtime_error_is_a_fault(broker, monkeypatch):
    """AC13: `Path.resolve()` raises RuntimeError, not OSError, on 3.11-3.12."""
    def loop(*_a, **_k):
        raise RuntimeError("Symlink loop")

    monkeypatch.setattr(pathlib.Path, "resolve", loop)
    with pytest.raises(broker.LockUnavailableError), broker._profile_lock("jira", budget_s=0.1):
        pass


# ----------------------------------------------------------------------
# AC15 — the held-set is keyed by (thread, profile).
# ----------------------------------------------------------------------


def test_nested_acquire_same_profile_raises_immediately(broker):
    """AC15: a same-thread re-acquire is a fault, and must not stall."""
    with broker._profile_lock("jira"):
        started = time.monotonic()
        with pytest.raises(broker.LockUnavailableError), broker._profile_lock("jira", budget_s=5):
            pass
        # The property is "the 5 s budget was not consumed". 1 s keeps 5x
        # headroom while surviving a throttled runner.
        assert time.monotonic() - started < 1.0


def test_nested_acquire_different_profile_also_raises(broker):
    """AC15: the rule is any-lock-held, not this-profile-held."""
    with broker._profile_lock("jira"):
        started = time.monotonic()
        with pytest.raises(broker.LockUnavailableError), broker._profile_lock("confluence", budget_s=5):
            pass
        # The property is "the 5 s budget was not consumed". 1 s keeps 5x
        # headroom while surviving a throttled runner.
        assert time.monotonic() - started < 1.0


def test_different_thread_contends_rather_than_faulting(broker):
    """AC15: the guard is thread-local, or the T2 harness is neutered.

    A process-global guard would make concurrent writers *raise* instead of
    contend, silently disabling the test the whole spec turns on.
    """
    outcome: list[str] = []
    holding = threading.Event()
    release = threading.Event()

    def hold():
        with broker._profile_lock("jira"):
            holding.set()
            release.wait(10)

    def contend():
        try:
            with broker._profile_lock("jira", budget_s=0.3):
                outcome.append("acquired")
        except broker.StoreContendedError:
            outcome.append("contended")
        except broker.LockUnavailableError:
            outcome.append("faulted")

    holder = threading.Thread(target=hold, daemon=True)
    holder.start()
    assert holding.wait(5)
    try:
        other = threading.Thread(target=contend, daemon=True)
        other.start()
        other.join(10)
    finally:
        release.set()
        holder.join(5)
    assert outcome == ["contended"], outcome


# ----------------------------------------------------------------------
# AC16 — the release path.
# ----------------------------------------------------------------------


def test_release_failure_does_not_replace_an_in_flight_exception(broker, monkeypatch):
    """AC16: StoreTransitionError names which keys still hold cookie bytes.

    An unlock that raises inside `finally` would replace it with an unrelated
    lock error, and the operator would never see which entries to remove.
    """
    monkeypatch.setattr(
        broker, "_release_once",
        lambda fd: (_ for _ in ()).throw(OSError(errno.EIO, "unlock failed")),
    )
    with (
        pytest.raises(broker.StoreTransitionError, match="the message that matters"),
        broker._profile_lock("jira"),
    ):
        raise broker.StoreTransitionError("the message that matters")


def test_unlock_reporting_not_locked_warns_without_raising(broker, monkeypatch, capsys):
    """AC16: the only runtime signal that the acquire silently never took.

    Windows-only. POSIX `flock(fd, LOCK_UN)` on an unlocked descriptor succeeds
    and cannot report the condition, so there is no POSIX arm to assert.
    """
    monkeypatch.setattr(
        broker, "_release_once",
        lambda fd: (_ for _ in ()).throw(
            PermissionError(errno.EACCES, "file already locked or unlocked")
        ),
    )
    with broker._profile_lock("jira"):
        pass
    assert "not locked" in capsys.readouterr().err.lower()


# ----------------------------------------------------------------------
# AC5 / AC21 — source-shape assertions and stdlib purity.
# ----------------------------------------------------------------------


def test_no_blocking_lock_call_survives_in_source():
    """AC5: only non-blocking acquires; the deadline is the engine's own.

    `flock(LOCK_EX)` blocks unboundedly and `msvcrt.locking(LK_LOCK)` caps
    itself at ten one-second attempts — neither honours a caller's budget.

    Parsed with `ast` rather than grepped: the prose in this module's own
    docstrings names `LK_LOCK` to explain why it is rejected, and a substring
    scan cannot tell an explanation from a call.
    """
    import ast

    tree = ast.parse(BROKER_PY.read_text(encoding="utf-8"))
    seen = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        target = getattr(node.func.value, "id", None), node.func.attr
        flags = {
            a.attr for a in ast.walk(node) if isinstance(a, ast.Attribute)
        }
        if target == ("fcntl", "flock"):
            seen += 1
            assert "LOCK_NB" in flags or "LOCK_UN" in flags, ast.dump(node)
        elif target == ("msvcrt", "locking"):
            seen += 1
            assert not {"LK_LOCK", "LK_RLCK"} & flags, ast.dump(node)
    assert seen >= 4, f"expected acquire+release on both platforms, saw {seen}"


def test_engine_imports_errno_and_threading():
    """AC21: `errno` is not imported today and every classifier branch needs it."""
    src = BROKER_PY.read_text(encoding="utf-8")
    assert "\nimport errno\n" in src
    assert "\nimport threading\n" in src
