"""Cross-process advisory lock for the state-file read-modify-write.

`safety.write_jailed` is atomic per-write (tmpfile + ``os.replace``), but the
*command-level* read-modify-write of the single ``~/.agentbundle/state.toml``
is not atomic across processes: two concurrent ``install`` runs each load a
stale snapshot and the second ``os.replace`` drops the first's adapter row
(a lost update — not file corruption, but corruption of intent). RFC-0052's
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
import time
from pathlib import Path
from typing import Callable, Iterator


class StateLockTimeout(OSError):
    """Raised when the lock cannot be acquired within the timeout."""


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
    contenders spin-retry every *poll* seconds up to *timeout*. A lockfile
    whose mtime is older than *stale_after* is reclaimed (a previous holder
    crashed); this prevents a permanent deadlock without a daemon.

    Raises ``StateLockTimeout`` if the lock cannot be acquired in time.
    """
    lock_path = state_path.with_name(state_path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    fd: int | None = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            # Reclaim a stale lock (holder crashed) by age, then retry.
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > stale_after:
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                # Holder released between our open and stat — retry promptly.
                continue
            if time.monotonic() >= deadline:
                raise StateLockTimeout(
                    f"could not acquire state lock {lock_path} within {timeout}s"
                )
            time.sleep(poll)
    try:
        with contextlib.suppress(OSError):
            os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        fd = None
        yield lock_path
    finally:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        lock_path.unlink(missing_ok=True)


def persist_state_locked(
    state_path: Path,
    mutate: Callable[["object"], None],
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
        mutate(state)
        safety.write_jailed(
            root,
            relpath,
            config.dump_state(state),
            scope=scope,
            allowed_prefixes=allowed_prefixes,
        )
    return state
