"""Cross-process advisory lock for a state-file read-modify-write.

**This module is the single authored source for two consumers** (ADR-0074). It
is projected byte-faithfully to
``packs/core/.apm/skills/work-loop/scripts/_statelock.py`` by
``agentbundle.build.skill_libs``, so it must import **only the standard
library** — no ``agentbundle`` import, direct or lazy. The projected copy runs in
adopter trees where this package is not installed. ``make build-check`` gates
the copy against this file.

The problem it solves: writing a state file atomically (``mkstemp`` +
``os.replace``) does not make the *command-level* read-modify-write atomic. Two
concurrent verbs each load a stale snapshot and the second replace drops the
first's update — a lost update, not file corruption, but corruption of intent.
Worse for a state machine: both callers validate against the same snapshot, so
one is admitted a transition that should have been refused.

Hardening over ``statelock.state_lock``, which this supersedes for new callers:

* **Every** retry path checks the deadline and sleeps. The older loop's
  ``except FileNotFoundError: continue`` does neither, and ``Path.stat()``
  follows a symlink — so a dangling symlink at the lock path spins at ~98% CPU
  forever and the timeout never fires. Here the examine step uses ``os.lstat``
  and refuses any non-regular file outright: waiting cannot make it acquirable.
* **Reclaim re-checks inode identity.** Rename alone is not enough. Contender B
  observes a stale lock; A reclaims it, unlinks, and creates a fresh lock; B then
  renames *A's live lock* away and acquires — two holders. So the reclaim renames
  to a per-attempt unique name, confirms the moved file is the one it judged
  stale, and puts it back if it is not.
* **Release keys on identity, not content**, and reports when its lockfile is
  gone or foreign (``StateLockLost``) instead of unlinking a successor's file and
  exiting quietly. This is what protects the *state* rather than the file: a
  holder whose lock was reclaimed mid-body must not report success.
* **No ``mkdir``.** The older helper creates the lock's parent, which is safe
  only for a confined state path. A caller whose path is unconfined would gain an
  arbitrary-directory-creation side effect on a path it then refuses.
* **Errors do not derive from ``OSError``.** Both consumers of the projected copy
  carry broad ``except OSError`` / ``except Exception`` handlers around the
  regions that take this lock, so an ``OSError``-derived lock failure is one
  boundary-drift away from being swallowed into an unlocked write.

No symlink is created (the repo's no-symlink posture), no daemon, no heartbeat,
no third-party import.
"""

from __future__ import annotations

import contextlib
import os
import re
import stat
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

__all__ = [
    "StateLockError",
    "StateLockTimeout",
    "StateLockUnusable",
    "StateLockLost",
    "exclusive",
]

# The lockfile holds exactly one line: a format tag, this module's per-hold
# token, and the holder's pid. Anything else is not ours — the reclaim path
# refuses to touch it, so the lock never deletes a file it did not write.
_RECORD_RE = re.compile(r"\Astatelock1 ([0-9a-f]{32}) ([0-9]{1,10})\n\Z")
_RECORD_TAG = "statelock1"

# Cap the read. The bytes end up in an operator-facing message, so they are
# bounded and pattern-validated before rendering rather than echoed.
_MAX_RECORD_BYTES = 256

# Defaults. These three are ONE budget, not three knobs:
#   timeout < maximum hold < stale_after
# `timeout` must be shorter than a legitimate hold or contenders give up on a
# live holder; `stale_after` must exceed one or a live holder is judged dead and
# a second writer is admitted. Consumers that hold the lock across subprocesses
# are responsible for bounding those calls so "maximum hold" is provable.
DEFAULT_TIMEOUT = 10.0
DEFAULT_STALE_AFTER = 300.0
DEFAULT_POLL = 0.05


class StateLockError(Exception):
    """Base for every lock failure.

    Deliberately not an ``OSError`` — see the module docstring.
    """


class StateLockTimeout(StateLockError):
    """Contended: someone holds it. Retrying later may succeed."""


class StateLockUnusable(StateLockError):
    """The lock path can never be acquired (not a regular file). Do not wait."""


class StateLockLost(StateLockError):
    """The lock was not ours at release — a reclaim took it mid-body.

    The mutation the caller performed may not reflect the state it decided
    from, so the caller must report failure rather than exiting 0.
    """


def lock_path_for(path: Path) -> Path:
    """The sibling lockfile guarding *path*."""
    return path.with_name(path.name + ".lock")


def _read_holder_pid(lock: Path) -> str | None:
    """The holder pid from a lockfile this module wrote, else None.

    None means "not a record we recognise" — either foreign content or a
    partially written one. Callers must not reclaim on None.
    """
    try:
        with Path(lock).open("rb") as fh:
            raw = fh.read(_MAX_RECORD_BYTES + 1)
    except OSError:
        return None
    if len(raw) > _MAX_RECORD_BYTES:
        return None
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    match = _RECORD_RE.match(text)
    return match.group(2) if match else None


def _reclaim(lock: Path, observed: os.stat_result) -> None:
    """Best-effort removal of the stale lockfile *observed*.

    Rename to a per-attempt unique name — unique per *attempt*, not per pid, so
    two threads of one process cannot collide — then confirm the file that moved
    is the one judged stale before unlinking it. On a mismatch we moved a live
    lock: put it back. Any residual window is caught at the other end by
    :class:`StateLockLost`.
    """
    claimed = lock.with_name(f"{lock.name}.reclaim.{uuid.uuid4().hex}")
    try:
        Path(lock).rename(claimed)
    except OSError:
        return  # another contender reclaimed, or the holder released first
    try:
        moved = os.lstat(claimed)
    except OSError:
        return
    if (moved.st_dev, moved.st_ino) != (observed.st_dev, observed.st_ino):
        # Not the file we judged stale — a live holder's. Restore it.
        with contextlib.suppress(OSError):
            Path(claimed).rename(lock)
        return
    with contextlib.suppress(OSError):
        Path(claimed).unlink()


def _release(lock: Path, ident: tuple[int, int]) -> bool:
    """Unlink *lock* iff it is still the file we created. True == lock lost.

    Identity, not content: a truncate-in-place rewrite keeps the inode, and
    comparing bytes would reject this check's own stronger form.
    """
    try:
        current = os.lstat(lock)
    except OSError:
        return True  # gone — someone reclaimed it
    if (current.st_dev, current.st_ino) != ident:
        return True  # a successor's file — leave it alone
    with contextlib.suppress(OSError):
        Path(lock).unlink()
    return False


@contextlib.contextmanager
def exclusive(
    path: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    stale_after: float = DEFAULT_STALE_AFTER,
    poll: float = DEFAULT_POLL,
) -> Iterator[Path]:
    """Hold an exclusive lock on ``<path>.lock`` for the duration of the block.

    Open the critical section *before* the read whose decision the write
    depends on, and close it *after* the write. Locking only read→write leaves
    the lost-update and admitted-transition defects intact, because both
    contenders still evaluate their guards against the same stale snapshot.

    Raises :class:`StateLockUnusable` at once if the lock path is not a regular
    file, :class:`StateLockTimeout` if contention outlasts *timeout*,
    :class:`StateLockError` for any other acquisition failure, and
    :class:`StateLockLost` after the block if the lock was reclaimed mid-body.
    Never creates a directory.
    """
    lock = lock_path_for(path)
    deadline = time.monotonic() + timeout
    record = f"{_RECORD_TAG} {uuid.uuid4().hex} {os.getpid()}\n".encode("ascii")
    holder: str | None = None
    unrecognised = False

    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            try:
                observed = os.lstat(lock)
            except FileNotFoundError:
                # Released between our open and our lstat. Retry — but bounded,
                # which is precisely what the superseded implementation missed.
                if time.monotonic() >= deadline:
                    raise StateLockTimeout(
                        f"could not acquire {lock} within {timeout}s"
                    ) from None
                time.sleep(poll)
                continue
            except OSError as exc:
                raise StateLockError(f"could not examine {lock}: {exc}") from exc

            if not stat.S_ISREG(observed.st_mode):
                raise StateLockUnusable(
                    f"refusing {lock}: a lock path must be a regular file "
                    f"(found mode {stat.filemode(observed.st_mode)}). Waiting "
                    "cannot make this acquirable — remove it."
                ) from None

            holder = _read_holder_pid(lock)
            unrecognised = holder is None
            # Staleness is wall-clock (st_mtime), unlike the monotonic timeout,
            # so it is exposed to NTP skew; the stale_after margin absorbs it.
            age = time.time() - observed.st_mtime
            if age > stale_after and not unrecognised:
                _reclaim(lock, observed)
                if time.monotonic() >= deadline:
                    raise StateLockTimeout(
                        f"could not acquire {lock} within {timeout}s"
                    ) from None
                # Sleep here too. A reclaim that keeps losing its rename would
                # otherwise spin hot until the deadline — bounded, but still the
                # CPU burn this module exists to have removed.
                time.sleep(poll)
                continue

            if time.monotonic() >= deadline:
                if unrecognised:
                    raise StateLockTimeout(
                        f"could not acquire {lock} within {timeout}s: it holds "
                        "no record this tool wrote, so it was not reclaimed. "
                        "Inspect it and remove it by hand if the run is dead."
                    ) from None
                raise StateLockTimeout(
                    f"could not acquire {lock} within {timeout}s (held by pid "
                    f"{holder}). If that process is gone, the lock is reclaimed "
                    f"automatically after {stale_after:.0f}s, or remove it."
                ) from None
            time.sleep(poll)
        except OSError as exc:
            # EACCES, EROFS, ENOSPC, IsADirectoryError on some platforms.
            # Fail closed through our own base so no broad `except OSError` in a
            # consumer can swallow it into an unlocked write.
            raise StateLockError(f"could not create lock {lock}: {exc}") from exc

    try:
        os.write(fd, record)
        held = os.fstat(fd)
        ident = (held.st_dev, held.st_ino)
    except OSError as exc:
        # An empty or partial lockfile can never be recognised at release, so it
        # would wedge every later verb until stale_after. Remove it and refuse.
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            Path(lock).unlink()
        raise StateLockError(
            f"could not write the lock record to {lock}: {exc}"
        ) from exc
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)

    lost = False
    try:
        yield lock
    finally:
        lost = _release(lock, ident)
    # Only reached when the body completed. If the body raised, that exception
    # propagates out of the try/finally and is not masked by this one.
    if lost:
        raise StateLockLost(
            f"lost {lock} mid-mutation: it was reclaimed as stale by another "
            "process, so a concurrent write may have overwritten this one. The "
            "state file may not reflect this run."
        )
