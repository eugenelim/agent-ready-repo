"""Cross-process advisory lock for the state-file read-modify-write.

`safety.write_jailed` is atomic per-write (tmpfile + ``os.replace``), but the
*command-level* read-modify-write of the single ``~/.agentbundle/state.toml``
is not atomic across processes: two concurrent ``install`` runs each load a
stale snapshot and the second ``os.replace`` drops the first's adapter row
(a lost update — not file corruption, but corruption of intent). The
concurrency AC requires that two simultaneous installs of different adapter
rows of one pack **both** land.

This module provides a stdlib-only, dependency-free, cross-platform lock
(``O_CREAT | O_EXCL`` lockfile with bounded retry + stale reclaim) and a
``persist_state_locked`` helper that performs the *whole* read-merge-write
under the lock — re-reading the latest state so a concurrent run's row is
merged rather than overwritten. No symlink is used (the repo's no-symlink
posture).
"""

from __future__ import annotations

import contextlib
import os
import re
import stat
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator

if TYPE_CHECKING:
    from agentbundle.config import State


class StateLockTimeout(OSError):
    """Raised when the lock cannot be acquired within the timeout."""


class StateLockUnusable(OSError):
    """Raised when the lock path can never become acquirable.

    Distinct from :class:`StateLockTimeout` because waiting cannot help: a
    non-regular file at the lock path (a symlink, a directory, a FIFO) will
    still be there at the deadline. Both subclass ``OSError``, which every
    caller of this module already handles.
    """


# Ownership record: a tag, a per-hold uuid4 token, and the holder's pid.
# The token is what makes ownership checkable — inode identity alone is not
# enough, because ext4 and tmpfs reuse inode numbers aggressively, so a
# successor's lockfile can land on the freed inode of the one being checked.
_RECORD_TAG = b"agentbundle-statelock"
# `O_BINARY` exists only on Windows; on POSIX the flags are unchanged.
_LOCK_OPEN_FLAGS = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
_RECORD_RE = re.compile(r"^agentbundle-statelock ([0-9a-f]{32}) (\d+)$")


def _read_record(lock: Path) -> bytes | None:
    """First line of *lock*, or ``None`` if unreadable."""
    try:
        with open(lock, "rb") as handle:  # noqa: PTH123 — need the raw fd path
            return handle.readline()
    except OSError:
        return None


def _same_file(st: os.stat_result, ident: tuple[int, int]) -> bool:
    """Inode identity. Necessary but not sufficient — see :func:`_is_ours`."""
    return (st.st_dev, st.st_ino) == ident


def _is_ours(lock: Path, ident: tuple[int, int], record: bytes) -> bool:
    """True iff *lock* is still the exact file this hold created."""
    try:
        st = os.lstat(lock)
    except OSError:
        return False
    return _same_file(st, ident) and _read_record(lock) == record


def _reclaim(lock: Path, observed: os.stat_result, record: bytes | None) -> None:
    """Best-effort removal of the stale lockfile *observed*.

    Rename to a name unique per *attempt* (not per pid — two threads of one
    process would otherwise collide), then confirm the file that moved is the
    one judged stale before unlinking it.

    On a mismatch we moved a *live* holder's lock, so it goes back by
    ``os.link``, not ``rename``: ``rename`` silently replaces its destination,
    so if a third process took the momentarily-free path in the meantime,
    restoring by rename would delete that process's lockfile and admit two
    holders. ``link`` fails with ``FileExistsError`` instead, and the displaced
    holder discovers the loss at release rather than a bystander losing a write.
    """
    claimed = lock.with_name(f"{lock.name}.reclaim.{uuid.uuid4().hex}")
    try:
        lock.rename(claimed)
    except OSError:
        return  # another contender reclaimed, or the holder released first
    try:
        moved = os.lstat(claimed)
    except OSError:
        return
    if not _same_file(moved, (observed.st_dev, observed.st_ino)) or (
        _read_record(claimed) != record
    ):
        try:
            os.link(claimed, lock)
        except OSError:
            # The path is occupied again, or the link failed; leaving `claimed`
            # in place fails closed rather than clobbering a live holder.
            return
        with contextlib.suppress(OSError):
            claimed.unlink()
        return
    with contextlib.suppress(OSError):
        claimed.unlink()


@contextlib.contextmanager
def state_lock(
    state_path: Path,
    *,
    timeout: float = 10.0,
    stale_after: float = 60.0,
    poll: float = 0.05,
) -> Iterator[Path]:
    """Hold an exclusive lock for *state_path* for the duration of the block.

    The lock is a sibling file ``<state_path>.lock`` created with
    ``O_CREAT | O_EXCL`` — the create succeeds for exactly one holder. Other
    contenders retry every *poll* seconds up to *timeout*. A lockfile whose
    mtime is older than *stale_after* is reclaimed (a previous holder crashed);
    this prevents a permanent deadlock without a daemon.

    **Every** retry path checks the deadline and sleeps. An earlier version did
    not: a *dangling symlink* at the lock path made ``O_CREAT | O_EXCL`` fail
    with ``FileExistsError`` while ``Path.stat()`` followed the link and raised
    ``FileNotFoundError``, whose handler looped with neither check nor sleep.
    One planted file wedged every state-mutating verb at 100% CPU, and the
    timeout never fired.

    The examine step therefore uses ``os.lstat`` (which does not follow) and
    refuses any lock path that is not a regular file — waiting cannot make a
    symlink acquirable.

    Raises :class:`StateLockUnusable` at once if the lock path is not a regular
    file, and :class:`StateLockTimeout` if contention outlasts *timeout*.
    """
    # ``state_path`` is trusted, CLI-resolved input (the repo root or
    # ``~/.agentbundle/``), never pack-sourced — so the sibling lock path
    # cannot be steered outside the jail. A future caller passing an
    # untrusted ``state_path`` would need its own confinement check.
    lock_path = state_path.with_name(state_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    record = b"%s %s %d\n" % (
        _RECORD_TAG,
        uuid.uuid4().hex.encode("ascii"),
        os.getpid(),
    )
    fd: int | None = None
    while True:
        try:
            # `O_BINARY` matters on Windows and is absent elsewhere. Without
            # it the CRT opens in TEXT mode and translates the `\n` ending the
            # ownership record into `\r\n` on write, while `_read_record`
            # reads binary — so `_is_ours` compared `...\r\n` against
            # `...\n`, judged the lockfile to be someone else's, and skipped
            # the unlink. Every hold leaked its lockfile, and the next state
            # write in the same 10-second window timed out waiting for a lock
            # nobody held.
            fd = os.open(lock_path, _LOCK_OPEN_FLAGS, 0o600)
            break
        except FileExistsError:
            try:
                observed = os.lstat(lock_path)
            except FileNotFoundError:
                # Released between our open and our lstat. Retry — BOUNDED,
                # which is exactly what the superseded loop missed.
                if time.monotonic() >= deadline:
                    raise StateLockTimeout(
                        f"could not acquire state lock {lock_path} within {timeout}s"
                    ) from None
                time.sleep(poll)
                continue

            if not stat.S_ISREG(observed.st_mode):
                raise StateLockUnusable(
                    f"refusing state lock {lock_path}: a lock path must be a "
                    f"regular file (found mode {stat.filemode(observed.st_mode)}). "
                    "Waiting cannot make this acquirable — remove it."
                ) from None

            observed_record = _read_record(lock_path)
            # Staleness is wall-clock (st_mtime), unlike the monotonic timeout,
            # so it is exposed to NTP skew; the stale_after margin absorbs it.
            age = time.time() - observed.st_mtime
            if age > stale_after:
                _reclaim(lock_path, observed, observed_record)
                if time.monotonic() >= deadline:
                    raise StateLockTimeout(
                        f"could not acquire state lock {lock_path} within {timeout}s"
                    ) from None
                # Sleep here too: a reclaim that keeps losing its rename would
                # otherwise spin hot until the deadline — bounded, but still the
                # CPU burn this hardening exists to remove.
                time.sleep(poll)
                continue

            if time.monotonic() >= deadline:
                raise StateLockTimeout(
                    f"could not acquire state lock {lock_path} within {timeout}s"
                ) from None
            time.sleep(poll)
    try:
        with contextlib.suppress(OSError):
            os.write(fd, record)
        os.close(fd)
        fd = None
        held = os.lstat(lock_path)
        ident = (held.st_dev, held.st_ino)
        yield lock_path
    finally:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        # Unlink only if this is still the file we created. The old code
        # unlinked unconditionally, so a hold whose lock had been reclaimed
        # would delete its *successor's* live lockfile on the way out — two
        # holders inside the section, from a release rather than an acquire.
        if _is_ours(lock_path, ident, record):
            with contextlib.suppress(OSError):
                lock_path.unlink()


def persist_state_locked(
    state_path: Path,
    mutate: Callable[[State], None],
    *,
    scope: str = "repo",
    allowed_prefixes: list[str] | None = None,
    root: Path | None = None,
    relpath: str | None = None,
    timeout: float = 10.0,
):
    """Apply *mutate* to the latest state and persist it, all under the lock.

    Under :func:`state_lock`, RE-READ the current state from disk (so a
    concurrent run's row is merged, not lost), call ``mutate(state)`` (which
    inserts/replaces this run's ``(pack, adapter)`` row and may set
    ``state.schema_version``), then write atomically via
    ``safety.write_jailed``. Returns the resulting ``State``.

    ``load_state`` raises ``StateFileLegacy`` on a non-current schema; that
    propagates to the caller (which renders the refuse-and-explain).
    """
    # Lazy imports keep CLI --version fast (repo convention).
    from agentbundle import config, safety

    if root is None:
        root = state_path.parent
    if relpath is None:
        relpath = state_path.name

    with state_lock(state_path, timeout=timeout):
        state = config.load_state(state_path, for_write=True)
        existing_version = state.schema_version
        mutate(state)
        # AC12: the floor is computed against the state re-read *inside* the
        # lock, never a pre-lock snapshot. A concurrent run that raised the file
        # to 0.5 between our read and our write would otherwise be silently
        # downgraded back to 0.4 by this write, stranding its direct rows.
        state.schema_version = direct_state_floor(existing_version, state)
        safety.write_jailed(
            root,
            relpath,
            config.dump_state(state),
            scope=scope,
            allowed_prefixes=allowed_prefixes,
        )
    return state


def direct_state_floor(existing_version: str, state) -> str:
    """Return the schema version to write: `max(existing, 0.5 if direct)`.

    Separated from :func:`persist_state_locked` so it can be driven directly,
    but it is deliberately not a general comparison: only two versions exist,
    and 0.5 is never downgraded to 0.4 even when the mutation being applied
    touches no direct row. A file reaches 0.5 because it holds direct
    provenance some earlier install wrote, and that provenance does not stop
    existing because this run installed a catalogue pack.
    """

    from agentbundle import config

    if existing_version == config.DIRECT_STATE_SCHEMA_VERSION:
        return config.DIRECT_STATE_SCHEMA_VERSION
    if state_carries_direct_rows(state):
        return config.DIRECT_STATE_SCHEMA_VERSION
    return config.STATE_SCHEMA_VERSION


def state_carries_direct_rows(state) -> bool:
    """True when any row records direct-source provenance."""

    # `State.packs` is flat and keyed by `(pack_name, adapter)`, not nested.
    return any(
        getattr(row, "source_kind", None) in {"pack", "skill"}
        for row in getattr(state, "packs", {}).values()
    )
