"""The four hardening properties of the state lock.

The defect that motivated these: a **dangling symlink** planted at the lock
path wedged every state-mutating verb. `os.open(O_CREAT|O_EXCL)` fails
`FileExistsError` on a symlink, while `Path.stat()` *follows* it and raises
`FileNotFoundError` — and that handler looped with neither a deadline check nor
a sleep. Confirmed against the shipped package before the fix: 100% CPU, still
spinning well past a 2-second timeout, which therefore never fired. One planted
file, every verb.

Each property below is stated as its own test, so a regression names which one
came back rather than only that something did.
"""

from __future__ import annotations

import os
import signal
import time
from pathlib import Path

import pytest
from agentbundle import statelock


def _state(tmp_path: Path) -> Path:
    p = tmp_path / "state.json"
    p.write_text("{}", encoding="utf-8")
    return p


def _lock_of(state: Path) -> Path:
    return state.with_name(state.name + ".lock")


class _Alarm:
    """Fail the test if the block outlasts *seconds* — a spin never returns."""

    def __init__(self, seconds: int) -> None:
        self.seconds = seconds

    def __enter__(self):
        if not hasattr(signal, "SIGALRM"):
            pytest.skip("SIGALRM unavailable on this platform")

        def _boom(_sig, _frm):
            raise AssertionError(
                "the acquire loop did not return — it is spinning, which is "
                "the exact defect these tests exist to prevent"
            )

        self._prev = signal.signal(signal.SIGALRM, _boom)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, *exc):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self._prev)
        return False


# --- 1. Every retry path checks the deadline and sleeps --------------------


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_a_dangling_symlink_lock_path_does_not_spin(tmp_path: Path) -> None:
    state = _state(tmp_path)
    _lock_of(state).symlink_to(tmp_path / "does-not-exist")

    started = time.monotonic()
    with _Alarm(10), pytest.raises(OSError), statelock.state_lock(state, timeout=2.0):
        pass
    assert time.monotonic() - started < 5.0, "took far longer than the timeout"


# --- 2. os.lstat + refuse a non-regular lock path --------------------------


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_a_symlink_lock_path_is_refused_not_waited_on(tmp_path: Path) -> None:
    """Waiting cannot make a symlink acquirable, so it must not be waited on.

    The distinction matters operationally: a timeout tells the operator to try
    again, which will never work. This tells them to remove the file.
    """
    state = _state(tmp_path)
    (tmp_path / "real-target").write_text("x", encoding="utf-8")
    _lock_of(state).symlink_to(tmp_path / "real-target")

    started = time.monotonic()
    with (
        _Alarm(10),
        pytest.raises(statelock.StateLockUnusable) as exc,
        statelock.state_lock(state, timeout=30.0),
    ):
        pass
    # Refused immediately, not after the 30s timeout.
    assert time.monotonic() - started < 2.0
    assert "regular file" in str(exc.value)


def test_a_directory_lock_path_is_refused(tmp_path: Path) -> None:
    state = _state(tmp_path)
    _lock_of(state).mkdir()
    with (
        _Alarm(10),
        pytest.raises(statelock.StateLockUnusable),
        statelock.state_lock(state, timeout=30.0),
    ):
        pass


def test_unusable_is_an_oserror(tmp_path: Path) -> None:
    """Both consumers handle OSError-family failures; keep it that way."""
    assert issubclass(statelock.StateLockUnusable, OSError)
    assert issubclass(statelock.StateLockTimeout, OSError)


# --- 3. Ownership keys on inode identity AND the per-hold token ------------


def test_release_does_not_unlink_a_successors_lock(tmp_path: Path) -> None:
    """The release-side half of the same class of bug.

    If a hold's lockfile is reclaimed mid-body and a successor takes the path,
    an unconditional `unlink()` on the way out deletes the *successor's* live
    lock — two holders inside the section, produced by a release rather than an
    acquire.
    """
    state = _state(tmp_path)
    lock = _lock_of(state)

    with statelock.state_lock(state, timeout=5.0):
        # Simulate the reclaim: our lockfile goes away and a successor's
        # appears at the same path with different contents.
        lock.unlink()
        lock.write_text("successor-holds-this\n", encoding="utf-8")

    assert lock.exists(), "release deleted a lockfile it did not create"
    assert lock.read_text(encoding="utf-8") == "successor-holds-this\n"


def test_release_removes_its_own_lock(tmp_path: Path) -> None:
    """The other direction — ownership checking must not leak locks."""
    state = _state(tmp_path)
    lock = _lock_of(state)
    with statelock.state_lock(state, timeout=5.0):
        assert lock.exists()
    assert not lock.exists(), "a normal release must remove its own lockfile"


def test_the_lock_record_identifies_this_hold(tmp_path: Path) -> None:
    state = _state(tmp_path)
    lock = _lock_of(state)
    with statelock.state_lock(state, timeout=5.0):
        record = lock.read_text(encoding="ascii")
    assert record.startswith("agentbundle-statelock ")
    assert record.rstrip().endswith(str(os.getpid()))


# --- 4. Stale reclaim still works -----------------------------------------


def test_a_stale_lock_is_still_reclaimed(tmp_path: Path) -> None:
    """Hardening must not cost the deadlock recovery it was built around."""
    state = _state(tmp_path)
    lock = _lock_of(state)
    lock.write_text("agentbundle-statelock deadbeef 99999\n", encoding="ascii")
    os.utime(lock, (time.time() - 3600, time.time() - 3600))

    with _Alarm(15), statelock.state_lock(state, timeout=5.0, stale_after=60.0):
        pass  # acquired by reclaiming the hour-old lock


def test_a_fresh_foreign_lock_times_out(tmp_path: Path) -> None:
    """A lock that is merely held, not stale, is waited on and then times out."""
    state = _state(tmp_path)
    _lock_of(state).write_text("agentbundle-statelock cafe 12345\n", encoding="ascii")

    started = time.monotonic()
    with (
        _Alarm(15),
        pytest.raises(statelock.StateLockTimeout),
        statelock.state_lock(state, timeout=0.5, stale_after=9999),
    ):
        pass
    elapsed = time.monotonic() - started
    assert elapsed >= 0.4, "must actually wait rather than refuse at once"
    assert elapsed < 5.0
