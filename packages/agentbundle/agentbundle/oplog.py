"""Pack operation log — append-only JSONL writer.

Each pack has a ``<pack_dir>/ops.jsonl`` log recording installs, upgrades,
and other operations. Entries are appended atomically:

- POSIX: single ``os.write()`` to an ``O_CREAT|O_APPEND`` fd.  The kernel
  inode lock (``i_rwsem`` on Linux, vnode lock on macOS) serialises
  concurrent appends for writes bounded below ``_MAX_ENTRY = 4096`` bytes
  on local filesystems.  NFS is explicitly NOT covered — see ``write_entry``
  for the warning path.
- Windows: ``statelock.state_lock`` (the existing mutex used for state.toml).

Callers:
    from agentbundle.oplog import write_entry, EntryTooLargeError
    write_entry("atlassian", "install", src="git+https://example.com/")
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import UTC, datetime
from pathlib import Path

_POSIX = os.name == "posix"

# Practical per-entry byte cap.  NOT PIPE_BUF (which governs pipes/FIFOs,
# not regular files, and is only 512 on macOS).  This is a defensible
# maximum for a single atomic write on local ext4/APFS/NTFS; NFS is
# documented below as unsupported.
_MAX_ENTRY = 4096

# Keys reserved in the entry dict; using them in ``extra`` is an error.
_RESERVED_KEYS = frozenset({"action", "src", "dst", "ts"})


class EntryTooLargeError(ValueError):
    """Raised when the base entry fields alone exceed ``_MAX_ENTRY`` bytes."""

    def __init__(self, actual: int, limit: int) -> None:
        self.actual = actual
        self.limit = limit
        super().__init__(
            f"oplog entry exceeds size limit: {actual} bytes > {limit} bytes; "
            "shorten src/dst or avoid very long pack names"
        )


def _append_line(path: Path, line: bytes) -> None:
    """Append *line* (including trailing newline) to *path* atomically."""
    if _POSIX:
        # O_NOFOLLOW refuses a pre-planted symlink at the ops.jsonl path,
        # mirroring the lstat guard in make_pack_dir and user_state_path.
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(str(path), flags, 0o600)
        try:
            n = os.write(fd, line)
            if n != len(line):
                warnings.warn(
                    f"oplog partial write: wrote {n} of {len(line)} bytes to {path}; "
                    "entry may be corrupt",
                    RuntimeWarning,
                    stacklevel=4,
                )
        finally:
            os.close(fd)
    else:
        from agentbundle.statelock import state_lock

        # Guard against a pre-planted symlink on Windows (no O_NOFOLLOW).
        if path.exists() and path.is_symlink():
            raise OSError(f"refusing to write oplog to symlink {path}")
        with state_lock(path), path.open("ab") as f:
            f.write(line)


def write_entry(
    pack_name: str,
    action: str,
    src: str,
    dst: str | None = None,
    *,
    extra: dict | None = None,
    state: object = None,
    home: Path | None = None,
) -> None:
    """Append one structured operation entry to ``<pack_dir>/ops.jsonl``.

    The emitted JSON object has these fields (in order):
        action, src, [dst if not None], [extra fields...], ts

    ``ts`` is always last (ISO-8601, UTC).

    Args:
        pack_name: Pack slug; validated against slug grammar.
        action:    Short verb, e.g. ``"install"``, ``"upgrade"``.
        src:       Source URI or path the operation came from.
        dst:       Destination path (optional).
        extra:     Additional key/value pairs to include.  Keys must not
                   overlap with the reserved set (``action``, ``src``,
                   ``dst``, ``ts``); ``ValueError`` raised pre-I/O otherwise.
        state:     ``State`` instance for ``pack_dir`` resolution (optional).
        home:      Override home directory (for testing).

    Raises:
        ValueError: if *extra* contains a reserved key, or *pack_name*
                    fails slug grammar.
        EntryTooLargeError: if the base fields alone exceed ``_MAX_ENTRY``.
    """
    from agentbundle.config import pack_dir as _pack_dir

    if extra:
        bad = _RESERVED_KEYS & set(extra)
        if bad:
            raise ValueError(
                f"write_entry: extra keys overlap with reserved keys: {sorted(bad)}"
            )

    ts = datetime.now(UTC).isoformat()

    # Build base entry (no extra, no ts) to check size first.
    base: dict = {"action": action, "src": src}
    if dst is not None:
        base["dst"] = dst
    base["ts"] = ts
    base_bytes = json.dumps(base, separators=(",", ":")).encode() + b"\n"
    if len(base_bytes) > _MAX_ENTRY:
        raise EntryTooLargeError(len(base_bytes), _MAX_ENTRY)

    # Now build the full entry with extra fields.
    entry: dict = {"action": action, "src": src}
    if dst is not None:
        entry["dst"] = dst
    if extra:
        full: dict = {**entry, **extra, "ts": ts}
        full_bytes = json.dumps(full, separators=(",", ":")).encode() + b"\n"
        if len(full_bytes) > _MAX_ENTRY:
            # Extra fields overflow the cap; emit a truncated entry.
            # Re-check size: adding "_truncated":true may itself push a
            # near-limit base entry over _MAX_ENTRY.
            truncated_entry: dict = {"action": action, "src": src}
            if dst is not None:
                truncated_entry["dst"] = dst
            truncated_entry["_truncated"] = True
            truncated_entry["ts"] = ts
            truncated_bytes = (
                json.dumps(truncated_entry, separators=(",", ":")).encode() + b"\n"
            )
            if len(truncated_bytes) > _MAX_ENTRY:
                raise EntryTooLargeError(len(truncated_bytes), _MAX_ENTRY)
            entry = truncated_entry
        else:
            entry = full
    else:
        entry["ts"] = ts

    line = json.dumps(entry, separators=(",", ":")).encode() + b"\n"

    # Resolve the ops.jsonl path.
    ops_path = _pack_dir(pack_name, state=state, home=home) / "ops.jsonl"
    _append_line(ops_path, line)
