"""Characterise byte-range advisory locking, so a lease can be designed on fact.

This file exists to answer ONE question that cannot be answered on macOS or Linux:
does `msvcrt.locking` — which locks a single byte at the CURRENT FILE POSITION —
let a holder and a prober conflict when the holder locks after writing a payload?

The cooperative worktree lease deferred out of spec/worktree-runtime-hygiene AC6
uses "is this claim's lock still held?" as its liveness signal. On POSIX `flock`
locks the whole open file description and position is irrelevant, so the question
does not arise. On Windows it does, and getting it wrong is not a degradation: if a
held lock is invisible to a prober, every liveness probe reads NOT_LIVE, a live
peer's claim is reclaimed, and `clean --apply` deletes under a live mutator — the
exact failure the lease exists to prevent.

Scope of the claim: these cases measure `windows-latest` in GitHub Actions, which
is the runner CI uses. They are not a statement about every Windows filesystem;
network shares in particular may differ, and the POSIX cases here are a control,
not the subject.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

WINDOWS = os.name == "nt"
PAYLOAD = b'{"pid": 1234, "token": "abc"}'


def _lock_one_byte_here(handle) -> None:
    """Lock one byte at the handle's CURRENT position (Windows) or the file (POSIX)."""
    if WINDOWS:
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _probe_is_blocked(path: Path, *, seek_to_zero: bool) -> bool:
    """Report whether a second handle is refused the lock. Never holds one."""
    with path.open("r+b") as probe:
        if seek_to_zero:
            probe.seek(0)
        try:
            _lock_one_byte_here(probe)
        except OSError:
            return True
        # Release immediately: a probe must never retain a lock.
        if WINDOWS:
            import msvcrt

            msvcrt.locking(probe.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(probe.fileno(), fcntl.LOCK_UN)
        return False


@pytest.fixture
def claim_file() -> Path:
    """One fresh claim-shaped file per case, canonicalised once."""
    root = Path(tempfile.mkdtemp(prefix="lock-semantics-")).resolve()
    return root / "claim.lease"


def test_locking_after_a_write_without_seeking_is_the_documented_hazard(
    claim_file: Path,
) -> None:
    """MEASUREMENT, not a requirement: does write-then-lock hide the lock?

    This is the shape the deferred implementation had. It asserts nothing about
    which answer is correct — it records the answer so the design can stop
    guessing. On POSIX the lock covers the open file description, so the probe is
    blocked regardless of position and this reads True.
    """
    with claim_file.open("w+b") as holder:
        holder.write(PAYLOAD)
        holder.flush()
        # deliberately NOT seeking: position is now len(PAYLOAD)
        _lock_one_byte_here(holder)
        blocked_at_zero = _probe_is_blocked(claim_file, seek_to_zero=True)

    print(
        f"\nMEASURED [{sys.platform} / os.name={os.name}] "
        f"write-then-lock, probe at position 0 -> "
        f"{'blocked (lock visible)' if blocked_at_zero else 'NOT blocked (LOCK INVISIBLE)'}"
    )
    if not WINDOWS:
        assert blocked_at_zero, "POSIX control: flock must be position-independent"


@pytest.mark.skipif(not WINDOWS, reason="the hazard is specific to msvcrt byte ranges")
def test_windows_write_then_lock_hides_the_lock_from_a_probe(claim_file: Path) -> None:
    """Pin the hazard explicitly on Windows so its removal is a visible change.

    If this ever fails, `msvcrt.locking` stopped being position-relative and the
    lease's Windows branch can be simplified — which is worth noticing, not
    silently inheriting.
    """
    with claim_file.open("w+b") as holder:
        holder.write(PAYLOAD)
        holder.flush()
        _lock_one_byte_here(holder)
        assert _probe_is_blocked(claim_file, seek_to_zero=True) is False, (
            "msvcrt.locking appears position-independent now; revisit the lease's "
            "Windows branch, which exists only because it is not"
        )


def test_seeking_to_zero_in_both_paths_makes_a_held_lock_observable(
    claim_file: Path,
) -> None:
    """THE INVARIANT ANY LOCK-BASED LIVENESS SCHEME NEEDS, on every platform.

    Both sides lock byte zero, so holder and prober contend for the same range.
    This is the candidate fix. If it fails on Windows, byte-range locking cannot
    carry liveness there and the lease must report UNDETERMINABLE on that platform
    rather than a wrong answer — failing safe toward refusing, never toward
    deleting.
    """
    with claim_file.open("w+b") as holder:
        holder.write(PAYLOAD)
        holder.flush()
        holder.seek(0)
        _lock_one_byte_here(holder)

        assert _probe_is_blocked(claim_file, seek_to_zero=True) is True, (
            "a held claim lock was invisible to a prober even with both sides at "
            "byte zero; byte-range locking cannot carry liveness on this platform"
        )


def test_a_dead_holder_releases_the_lock(claim_file: Path) -> None:
    """The other half of the scheme: the OS must release on process death.

    Reclaiming a crashed run's claim is the whole reason liveness is a lock rather
    than a recorded process id, and this host reaps runs under memory pressure.
    """
    claim_file.write_bytes(PAYLOAD)
    holder_source = (
        "import os, sys\n"
        f"path = {str(claim_file)!r}\n"
        "handle = open(path, 'r+b')\n"
        "handle.seek(0)\n"
        "if os.name == 'nt':\n"
        "    import msvcrt; msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)\n"
        "else:\n"
        "    import fcntl; fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "print('LOCKED', flush=True)\n"
        "sys.stdin.read()\n"
    )
    holder = subprocess.Popen(
        [sys.executable, "-c", holder_source],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "LOCKED", "holder failed to start"
        assert _probe_is_blocked(claim_file, seek_to_zero=True) is True, (
            "a live holder's lock was not observable"
        )
    finally:
        holder.kill()
        holder.wait()

    assert _probe_is_blocked(claim_file, seek_to_zero=True) is False, (
        "the OS did not release a killed holder's lock; a crashed run would wedge "
        "the lease permanently"
    )


# The offset the shipped lease actually uses, imported rather than copied: a fixture
# measuring a duplicate of the constant would keep passing after the real one moved.
from tools.repo.coordination_lease import CLAIM_LOCK_OFFSET  # noqa: E402


def _hold_and_report(path: Path, offset: int) -> tuple[bool, bool]:
    """Hold a lock at `offset`, then report (probe_blocked, payload_readable)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PAYLOAD)
    with path.open("r+b") as holder:
        holder.seek(offset)
        _lock_one_byte_here(holder)
        try:
            with path.open("r+b") as probe:
                probe.seek(offset)
                try:
                    _lock_one_byte_here(probe)
                    blocked = False
                    if WINDOWS:
                        import msvcrt

                        msvcrt.locking(probe.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(probe.fileno(), fcntl.LOCK_UN)
                except OSError:
                    blocked = True
            try:
                readable = path.read_bytes() == PAYLOAD
            except OSError:
                readable = False
            return blocked, readable
        finally:
            if WINDOWS:
                import msvcrt

                holder.seek(offset)
                msvcrt.locking(holder.fileno(), msvcrt.LK_UNLCK, 1)


def test_the_shipped_offset_is_both_observable_and_leaves_the_payload_readable(
    claim_file: Path,
) -> None:
    """The lease's actual protocol, measured: both requirements at once.

    A claim lock has to satisfy two things that pull against each other. It must be
    observable to a prober, or every liveness probe reads not-live and cleanup deletes
    under a live mutator. And the payload must stay readable while it is held, because
    `_read_record` reads it to name a holder in a refusal. Byte zero satisfies the
    first and breaks the second on Windows, where the lock is mandatory rather than
    advisory -- measured as 9 `PermissionError` failures on windows-latest.
    """
    blocked, readable = _hold_and_report(claim_file, CLAIM_LOCK_OFFSET)
    print(
        f"MEASURED [{sys.platform} / os.name={os.name}] lock at CLAIM_LOCK_OFFSET"
        f"={CLAIM_LOCK_OFFSET} -> probe blocked={blocked}, payload readable={readable}",
        flush=True,
    )

    assert blocked, "a held claim lock must be observable to a prober"
    assert readable, "a held claim lock must not make the claim payload unreadable"


def test_locking_byte_zero_is_the_hazard_this_offset_exists_to_avoid(
    claim_file: Path,
) -> None:
    """Byte zero is inside the payload, and on Windows that makes it unreadable.

    Recorded as a measurement rather than a comment because it is the reason the
    offset is not zero, and because on POSIX it is invisible: `flock` is advisory, so
    the payload stays readable there and this case cannot fail on macOS. That is
    precisely why the byte-zero protocol passed a full local suite, sixteen mutation
    proofs and an adversarial review before a Windows runner rejected it.
    """
    blocked, readable = _hold_and_report(claim_file, 0)
    print(
        f"MEASURED [{sys.platform} / os.name={os.name}] lock at byte 0 -> "
        f"probe blocked={blocked}, payload readable={readable}",
        flush=True,
    )

    assert blocked, "byte zero is at least observable; that was never the problem"
    if WINDOWS:
        assert not readable, (
            "expected the mandatory Windows lock to deny the payload read; if this "
            "now passes, the platform behaviour changed and CLAIM_LOCK_OFFSET's "
            "rationale needs re-measuring rather than trusting"
        )
    else:
        assert readable, "POSIX flock is advisory, so the payload stays readable"
