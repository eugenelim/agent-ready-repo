"""Cross-process advisory lock for a state-file read-modify-write.

A project-knowledge script, owned by this skill. Stdlib only — no
``agentbundle`` import, direct or lazy — so it works in adopter trees and
user-scope installs where nothing else is on the path. Its siblings load it by
path (``importlib.util.spec_from_file_location`` against ``SCRIPT_DIR``), not by
``import``, because a plain import does not resolve under the importlib-based
test harnesses.

The problem it solves: writing a state file atomically (``mkstemp`` +
``os.replace``) does not make the *command-level* read-modify-write atomic. Two
concurrent verbs each load a stale snapshot and the second replace drops the
first's update — a lost update, not file corruption, but corruption of intent.
Worse for a state machine: both callers validate against the same snapshot, so
one is admitted a transition that should have been refused.

Hardening, each item a defect the older implementation still has:

* **Every** retry path checks the deadline and sleeps. The older loop's
  ``except FileNotFoundError: continue`` does neither, and ``Path.stat()``
  follows a symlink — so a dangling symlink at the lock path spins at ~98% CPU
  forever and the timeout never fires. Here the examine step uses ``os.lstat``
  and refuses any non-regular file outright: waiting cannot make it acquirable.
* **Reclaim and release key on inode identity AND the per-hold token.** Rename
  alone is not enough: contender B observes a stale lock; A reclaims it and
  creates a fresh one; B then renames *A's live lock* away and acquires — two
  holders. Inode identity alone is not enough either, because ext4 and tmpfs
  reuse inode numbers, so a successor's lockfile can land on the freed inode of
  the file being checked. Both together make a false match require reproducing a
  uuid4. A mismatched reclaim restores the file with ``os.link`` rather than
  ``rename``, since ``rename`` would silently replace — and so delete — a
  bystander's lockfile.
* **A holder that lost its lock says so** (``StateLockLost``) rather than
  unlinking a successor's file and exiting quietly. This is what protects the
  *state* rather than the file: a holder reclaimed mid-body must not report
  success, or the lost update is back with a green exit code.
* **A fresh empty lock is contended, not reclaimed.** ``O_CREAT|O_EXCL`` makes
  the path visible before the ownership record is written, so an empty record
  may belong to a live creator. It remains eligible for crash recovery, but
  only after the same ``stale_after`` budget as a complete recognised record.
* **No ``mkdir``.** Creating the lock's parent is safe only for a confined state
  path. Callers must create and confine the parent before entering the lock.
* **Errors do not derive from ``OSError``.** Both callers carry broad
  ``except OSError`` / ``except Exception`` handlers around the regions that take
  this lock, so an ``OSError``-derived failure is one boundary-drift away from
  being swallowed into an unlocked write.

No symlink is created (the repo's no-symlink posture), no daemon, no heartbeat,
no third-party import."""

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


def _read_record(lock: Path) -> bytes | None:
    """The raw record bytes, or None if the path is not a plain readable file.

    Opened ``O_NOFOLLOW`` so this is the one call on the lock path that cannot
    be redirected by a symlink planted after the ``S_ISREG`` check.
    """
    try:
        fd = os.open(lock, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        return None
    try:
        return os.read(fd, _MAX_RECORD_BYTES + 1)
    except OSError:
        return None
    finally:
        with contextlib.suppress(OSError):
            os.close(fd)


def _holder_pid(record: bytes | None) -> str | None:
    """The holder pid from a record this module wrote, else None.

    None means there is no complete record we recognise — foreign content, an
    in-progress create, or a create torn before its write. Never rendered into
    a message unvalidated.
    """
    if record is None or len(record) > _MAX_RECORD_BYTES:
        return None
    try:
        text = record.decode("ascii")
    except UnicodeDecodeError:
        return None
    match = _RECORD_RE.match(text)
    return match.group(2) if match else None


def _same_file(st: os.stat_result, ident: tuple[int, int]) -> bool:
    """Inode identity. Necessary but NOT sufficient — see :func:`_is_ours`."""
    return (st.st_dev, st.st_ino) == ident


def _is_ours(lock: Path, ident: tuple[int, int], record: bytes) -> bool:
    """True iff *lock* is still the exact file this hold created.

    Inode identity alone is not enough: ext4 and tmpfs reuse inode numbers
    aggressively, so a successor's lockfile can land on the freed inode of the
    file we are checking for. Matching the per-hold token as well makes a false
    positive require reproducing a uuid4, which is the point of the token.
    """
    try:
        st = os.lstat(lock)
    except OSError:
        return False
    return _same_file(st, ident) and _read_record(lock) == record


def _reclaim(lock: Path, observed: os.stat_result, record: bytes | None) -> None:
    """Best-effort removal of the stale lockfile *observed*.

    Rename to a per-attempt unique name — unique per *attempt*, not per pid, so
    two threads of one process cannot collide — then confirm the file that moved
    is the one judged stale before unlinking it.

    On a mismatch we moved a *live* holder's lock, so it has to go back. The
    restore uses ``os.link`` rather than ``rename``: ``rename`` silently replaces
    its destination, so if a third process took the momentarily-free lock path in
    the meantime, restoring by rename would delete that process's lockfile and
    leave two holders inside the section. ``link`` fails with ``FileExistsError``
    instead, and the displaced holder then discovers the loss at release
    (:class:`StateLockLost`) rather than a bystander losing a write silently.
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
    # Both inode identity AND the bytes we judged stale — inode reuse alone
    # would let this delete a foreign file created in the window.
    if not _same_file(moved, (observed.st_dev, observed.st_ino)) or (
        _read_record(claimed) != record
    ):
        try:
            os.link(claimed, lock)
        except FileExistsError:
            # The lock path is occupied again; leaving `claimed` where it is
            # fails closed — that holder reports StateLockLost at release.
            return
        except OSError:
            return
        with contextlib.suppress(OSError):
            Path(claimed).unlink()
        return
    with contextlib.suppress(OSError):
        Path(claimed).unlink()


def _release(lock: Path, ident: tuple[int, int], record: bytes) -> bool:
    """Unlink *lock* iff it is still the file we created. True == lock lost.

    Identity plus token, never content-equality-only and never inode-only: the
    first would reject a legitimate re-read, the second false-matches after
    inode reuse and would unlink a successor's live lock while reporting success.
    """
    if not _is_ours(lock, ident, record):
        return True  # gone, or a successor's — leave it alone and report
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

            observed_record = _read_record(lock)
            holder = _holder_pid(observed_record)
            # O_CREAT|O_EXCL publishes an empty file before this module writes
            # its ownership record. It may therefore be a live creator's lock,
            # not only a create torn by a crash. Recognise the empty intermediate
            # state so it remains eligible for stale recovery, but never reclaim
            # it before the same stale_after budget as a complete record.
            empty_record = observed_record == b""
            unrecognised = holder is None and not empty_record
            # Staleness is wall-clock (st_mtime), unlike the monotonic timeout,
            # so it is exposed to NTP skew; the stale_after margin absorbs it.
            age = time.time() - observed.st_mtime
            if age > stale_after and not unrecognised:
                _reclaim(lock, observed, observed_record)
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
                    detail = (
                        "it is not readable by this user "
                        f"(owner uid {observed.st_uid})"
                        if observed_record is None
                        else "it holds no record this tool wrote"
                    )
                    raise StateLockTimeout(
                        f"could not acquire {lock} within {timeout}s: {detail}, "
                        f"so it was not reclaimed. It is "
                        f"{time.time() - observed.st_mtime:.0f}s old; inspect it "
                        "and remove it by hand if the run is dead."
                    ) from None
                if empty_record:
                    raise StateLockTimeout(
                        f"could not acquire {lock} within {timeout}s: its "
                        "ownership record is not yet available. If its creator "
                        "is gone, the empty lock is reclaimed automatically "
                        f"after {stale_after:.0f}s, or remove it."
                    ) from None
                raise StateLockTimeout(
                    f"could not acquire {lock} within {timeout}s (recorded "
                    f"holder pid {holder}). If that process is gone, the lock is "
                    f"reclaimed automatically after {stale_after:.0f}s, or "
                    "remove it."
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
        lost = _release(lock, ident, record)
    # Only reached when the body completed. If the body raised, that exception
    # propagates out of the try/finally and is not masked by this one.
    if lost:
        raise StateLockLost(
            f"lost {lock} mid-mutation: it was reclaimed as stale by another "
            "process, so a concurrent write may have overwritten this one. The "
            "state file may not reflect this run."
        )
