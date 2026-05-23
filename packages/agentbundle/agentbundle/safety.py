"""Tier-1/2/3 file-safety primitives, path-jail enforcement, content hashing.

The Tier contract is owned by the sibling `distribution-adapters` spec.
Here we implement it:

  - Tier-1 — adapter-contract-projected; SHA in state matches on-disk.
            The CLI may write or overwrite.
  - Tier-2 — adapter-contract-projected; on-disk SHA differs from state
            (adopter has edited the file since install). The CLI never
            overwrites; it drops a `<stem>.upstream.<ext>` companion next
            to the original instead.
  - Tier-3 — every path the state file does not record under any pack.
            Read-only to the CLI.

`write_jailed` is the only sanctioned write call. Every command that
writes routes through it so the path-jail check (refusal of any
`../`-style escape from the configured root) is non-optional.
"""

from __future__ import annotations

import enum
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from agentbundle.config import State


class Tier(enum.Enum):
    TIER_1 = "tier-1"
    TIER_2 = "tier-2"
    TIER_3 = "tier-3"


class PathJailError(ValueError):
    """Raised when a write would land outside the configured root."""


class WriteError(OSError):
    """Raised when an otherwise-jailed write fails due to OS errors —
    typically `PermissionError` on a read-only filesystem, `OSError` on
    a full disk, or `NotADirectoryError` when a parent exists as a file.

    Distinct from `PathJailError` so callers can render different one-line
    stderr messages: jail violations indicate a malicious or buggy pack,
    write errors indicate environment problems on the adopter side.
    """


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------


def classify(relpath: str, root: Path, state: State) -> Tier:
    """Classify `relpath` (relative to `root`) per the Tier contract.

    Resolution:
      1. If `relpath` is in `state.projected_paths()`:
         - If the file is absent on disk → treat as Tier-1 (about to write).
         - If on-disk SHA == state SHA  → Tier-1.
         - Else                        → Tier-2 (adopter has edited).
      2. Otherwise → Tier-3.

    The "absent on disk → Tier-1" rule is important for `install` and
    `render` after a Tier-1 file was deleted by the adopter — re-installing
    rewrites it (it's adapter-contract space; the bundle owns it).

    **Carve-out for first-install paths:** `commands/install._classify_for_install`
    deliberately bypasses this function for the install command's own walk
    because step 2 here ("not in state → Tier-3") would mark every path
    in a fresh projection as Tier-3 on a first install, suppressing every
    write. The install command's contract is different — every path in
    its incoming projection is adapter-contract space, and the classifier
    only decides overwrite-vs-companion. Do not "fix" this function to do
    what install needs; install's contract differs.
    """
    if relpath not in state.projected_paths():
        return Tier.TIER_3

    on_disk = root / relpath
    if not on_disk.exists():
        return Tier.TIER_1

    expected_sha = None
    for ps in state.packs.values():
        sha = ps.file_sha(relpath)
        if sha:
            expected_sha = sha
            break
    if expected_sha is None:
        # Path recorded under a pack table but without a sha entry; we
        # can't prove tier-1 vs tier-2 — be conservative.
        return Tier.TIER_2

    return Tier.TIER_1 if sha256_file(on_disk) == expected_sha else Tier.TIER_2


# ---------------------------------------------------------------------------
# .upstream.<ext> companion paths
# ---------------------------------------------------------------------------


def companion_path(path: Path) -> Path:
    """Compute the `.upstream.<ext>` companion path for `path`.

    Rules (from the sibling spec § companion semantics):
      - `AGENTS.md`        → `AGENTS.upstream.md`
      - `docs/CHARTER.md`  → `docs/CHARTER.upstream.md`
      - `Makefile`         → `Makefile.upstream`  (no extension)
      - `foo.tar.gz`       → `foo.tar.upstream.gz`  (only the final suffix
                                                     is treated as the ext)
    """
    suffix = path.suffix  # always includes the leading "."; empty if none
    if suffix:
        return path.with_name(path.stem + ".upstream" + suffix)
    return path.with_name(path.name + ".upstream")


# ---------------------------------------------------------------------------
# Path-jail
# ---------------------------------------------------------------------------


def assert_under(root: Path, target: Path) -> None:
    """Refuse if `target.resolve()` would escape `root.resolve()`.

    Used by `write_jailed` and by recipe-loading sites that synthesise
    target paths from untrusted data (catalogue URIs, fixture packs).
    The resolved comparison foils `..` traversal and symlink escape.
    """
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathJailError(
            f"refusing to write outside repo root: {target_resolved} not under {root_resolved}"
        ) from exc


# ---------------------------------------------------------------------------
# Atomic, jailed writes
# ---------------------------------------------------------------------------


def write_jailed(root: Path, relpath: str, content: bytes | str, *, mode: int | None = None) -> Path:
    """Write `content` to `root / relpath` atomically; refuse outside-root.

    Atomic: writes to a sibling tmpfile then `os.replace`s into place. The
    rename is atomic on POSIX within a filesystem; we ensure same-fs by
    putting the tmpfile next to the target.

    Returns the final on-disk path (resolved). Raises `PathJailError` if
    the resolved target escapes `root`. Caller is responsible for any
    write_atomic backups / Tier-2 companion logic — `write_jailed` is the
    primitive, not the policy.
    """
    target = root / relpath
    assert_under(root, target)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WriteError(
            f"cannot create parent directory {target.parent}: {exc}"
        ) from exc

    if isinstance(content, str):
        data = content.encode("utf-8")
    else:
        data = content

    try:
        fd, tmp_str = tempfile.mkstemp(
            prefix=target.name + ".",
            suffix=".tmp",
            dir=str(target.parent),
        )
    except OSError as exc:
        raise WriteError(
            f"cannot write under {target.parent}: {exc}"
        ) from exc
    tmp = Path(tmp_str)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, target)
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise WriteError(
            f"cannot write {target}: {exc}"
        ) from exc
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return target.resolve()


def write_companion(root: Path, relpath: str, content: bytes | str) -> Path:
    """Write a `<stem>.upstream.<ext>` companion next to `relpath`."""
    companion = companion_path(Path(relpath))
    return write_jailed(root, str(companion), content)


def copy_jailed(root: Path, source: Path, relpath: str) -> Path:
    """Copy a file into the jailed root, preserving mode (mirrors shutil.copy2)."""
    target = root / relpath
    assert_under(root, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target, follow_symlinks=False)
    return target.resolve()


# ---------------------------------------------------------------------------
# Helpers used by commands that walk projections
# ---------------------------------------------------------------------------


def projected_files_in_state(state: State, pack_name: str) -> Iterable[str]:
    ps = state.packs.get(pack_name)
    if ps is None:
        return ()
    return tuple(ps.files.keys())
