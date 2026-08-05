"""Helpers for managing per-pack, per-worktree blocks in `.git/info/exclude`.

Used by ``agentbundle install --scope local`` (RFC-0080) to make
installed files git-invisible without committing anything. The core
invariant: a pack's files are excluded from git *before* they are
written to disk, and excluded *until* they are removed from disk.

Block format in the exclude file::

    # agentbundle:local:<pack>:<worktree-id>:begin
    /.claude/skills/<pack>/SKILL.md
    /.claude/agents/<pack>/AGENT.md
    # agentbundle:local:<pack>:<worktree-id>:end

Each path is written with a leading ``/`` anchor so it applies only
to the repo root (not recursively), and every gitignore metacharacter
(``[``, ``]``, ``*``, ``?``, ``\\``) is backslash-escaped before
writing so filenames containing pattern syntax are matched literally
and not as globs. The leading ``/`` anchor means ``#`` and ``!`` can
never appear at line start, so they need no escaping.

Concurrent-write limitation (AC26): two ``agentbundle`` processes
writing simultaneously use last-writer-wins semantics. The temp-file
``os.replace`` is atomic at the filesystem level but there is no
advisory lock; a race between two installs for different packs in the
same worktree can lose the earlier writer's block. This is a known
v1 limitation documented here and in the guides.

Cross-worktree side-effect (AC27):
  (a) **Live-worktree side-effect** — a leading-``/`` pattern in
      ``info/exclude`` excludes same-path untracked files in *all*
      linked worktrees, not just the installing one. This is a
      git-level behaviour of the shared ``info/exclude`` file.
  (b) **Stale-block risk** — when a worktree is deleted without
      running ``agentbundle uninstall --scope local`` first, the
      block remains in ``info/exclude`` and continues excluding
      same-path files in all remaining worktrees — including tracked
      or committed files added later. Run ``agentbundle local prune``
      (deferred v2 feature) to sweep orphaned blocks. This is a known
      v1 limitation.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Worktree-id derivation
# ---------------------------------------------------------------------------

_COLON_RE = re.compile(r":")
_PRIMARY_SENTINEL = "primary"


def _git_rev_parse(repo_root: Path, flag: str) -> str:
    """Run ``git -C <repo_root> rev-parse <flag>`` and return stripped stdout.

    Raises:
        RuntimeError: if git exits non-zero (not inside a work tree or git
            not installed).  Callers that want a graceful failure should catch
            this; callers that need a pre-flight bool should use
            :func:`is_git_repo` first.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", flag],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or f"git rev-parse {flag} failed (exit {result.returncode})"
        raise RuntimeError(msg)
    return result.stdout.strip()


def is_git_repo(repo_root: Path) -> bool:
    """Return True iff *repo_root* is inside a git work tree.

    Uses ``git rev-parse --is-inside-work-tree``; returns False for any
    non-zero exit (not a repo, git not installed, bare clone, etc.).
    Never raises.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def derive_worktree_id(repo_root: Path) -> str:
    """Derive a stable worktree identifier for this clone.

    For the primary worktree ``--git-dir`` and ``--git-common-dir``
    point to the same directory; return the sentinel ``"primary"``.

    For a linked worktree created by ``git worktree add``, ``--git-dir``
    resolves to ``<common>/.git/worktrees/<name>``; return the last path
    component (the worktree name), with any ``:`` characters replaced by
    ``_`` to keep the block-key parseable.

    Args:
        repo_root: the repository root to query (passed as ``-C`` so the
            call probes the target repo, not the process CWD).

    Returns:
        A string safe for use as the ``<worktree-id>`` segment of the
        exclude block key.
    """
    git_dir = _git_rev_parse(repo_root, "--git-dir")
    common_dir = _git_rev_parse(repo_root, "--git-common-dir")

    if git_dir == common_dir:
        return _PRIMARY_SENTINEL

    # Linked worktree: last component of the git-dir path
    wid = Path(git_dir).name
    return _COLON_RE.sub("_", wid)


# ---------------------------------------------------------------------------
# Gitignore metacharacter escaping
# ---------------------------------------------------------------------------

_GITIGNORE_META_RE = re.compile(r"([\[\]*?\\])")


def escape_gitignore_path(path: str) -> str:
    """Backslash-escape gitignore metacharacters in *path*.

    Escapes ``[``, ``]``, ``*``, ``?``, and ``\\``. The characters
    ``#`` and ``!`` are not escaped because all paths are written with
    a leading ``/`` anchor, which prevents them from appearing at line
    start where gitignore would interpret them specially.

    Args:
        path: the repo-relative path string (should start with ``/``).

    Returns:
        The escaped path string, safe for literal gitignore matching.
    """
    return _GITIGNORE_META_RE.sub(r"\\\1", path)


# ---------------------------------------------------------------------------
# Block key helpers
# ---------------------------------------------------------------------------

_BLOCK_KEY_RE = re.compile(r"^# agentbundle:local:([^:]+):([^:]+):(begin|end)\s*$")


def _begin_marker(pack: str, worktree_id: str) -> str:
    return f"# agentbundle:local:{pack}:{worktree_id}:begin"


def _end_marker(pack: str, worktree_id: str) -> str:
    return f"# agentbundle:local:{pack}:{worktree_id}:end"


# ---------------------------------------------------------------------------
# Atomic file write
# ---------------------------------------------------------------------------


def _write_atomically(path: Path, content: bytes) -> None:
    """Write *content* to *path* atomically via a temp file + ``os.replace``."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix=".agentbundle-exclude-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        Path(tmp).replace(path)
    except BaseException:
        import contextlib
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_exclude_block(
    exclude_path: Path,
    pack: str,
    worktree_id: str,
    patterns: list[str],
) -> None:
    """Write or replace the named pack's exclude block in *exclude_path*.

    The block is identified by ``(pack, worktree_id)``. If a block for
    this pair already exists it is replaced in place; otherwise the new
    block is appended. The caller passes the **union** of all adapter
    patterns for this pack (not just the current adapter's patterns) so
    the block always represents the full installed footprint.

    Each path in *patterns* is gitignore-metacharacter-escaped before
    writing (see :func:`escape_gitignore_path`).

    Concurrent-write limitation: two processes writing simultaneously
    use last-writer-wins. No advisory lock is held during the read-
    modify-write cycle; a race between installs for different packs can
    lose the earlier block. This is a known v1 limitation (AC26).

    Cross-worktree side-effect: a leading-``/`` pattern in the shared
    ``info/exclude`` file excludes the same untracked path in *all*
    linked worktrees, not just the installing one. When a worktree is
    deleted without uninstalling, its stale block continues to exclude
    same-path files in remaining worktrees — including files tracked or
    committed later. Run ``agentbundle local prune`` (deferred v2
    feature) to sweep orphaned blocks. This is a known v1 limitation
    (AC27).

    Args:
        exclude_path: absolute path to the ``info/exclude`` file; created
            if absent.
        pack: the pack name (used in the block key).
        worktree_id: the worktree identifier from :func:`derive_worktree_id`.
        patterns: repo-relative paths to exclude (should start with ``/``).
    """
    # Read current content (create if absent)
    if exclude_path.exists():
        old_content = exclude_path.read_text(encoding="utf-8", errors="surrogateescape")
        lines = old_content.splitlines(keepends=True)
    else:
        lines = []

    begin = _begin_marker(pack, worktree_id)
    end = _end_marker(pack, worktree_id)

    # Find existing block boundaries
    begin_idx = end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n").rstrip("\r")
        if stripped == begin:
            begin_idx = i
        elif stripped == end:
            end_idx = i

    escaped = [escape_gitignore_path(p) for p in patterns]
    new_block_lines: list[str] = (
        [begin + "\n"]
        + [p + "\n" for p in escaped]
        + [end + "\n"]
    )

    if begin_idx is not None and end_idx is not None:
        # Replace in place
        new_lines = lines[:begin_idx] + new_block_lines + lines[end_idx + 1:]
    else:
        # Append
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        new_lines = lines + new_block_lines

    _write_atomically(exclude_path, "".join(new_lines).encode("utf-8"))


def strip_exclude_block(
    exclude_path: Path,
    pack: str,
    worktree_id: str,
) -> None:
    """Remove the named pack's exclude block from *exclude_path*.

    Sibling blocks (other packs or other worktrees) are left intact.
    Call this only when the last adapter row for this pack is being
    removed; for multi-adapter packs, call :func:`write_exclude_block`
    with the remaining adapters' union patterns instead.

    If the block is not found, this is a no-op (idempotent).

    Args:
        exclude_path: absolute path to the ``info/exclude`` file.
        pack: the pack name.
        worktree_id: the worktree identifier.
    """
    if not exclude_path.exists():
        return

    old_content = exclude_path.read_text(encoding="utf-8", errors="surrogateescape")
    lines = old_content.splitlines(keepends=True)

    begin = _begin_marker(pack, worktree_id)
    end = _end_marker(pack, worktree_id)

    begin_idx = end_idx = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n").rstrip("\r")
        if stripped == begin:
            begin_idx = i
        elif stripped == end:
            end_idx = i

    if begin_idx is None or end_idx is None:
        return  # block not found — no-op

    new_lines = lines[:begin_idx] + lines[end_idx + 1:]
    _write_atomically(exclude_path, "".join(new_lines).encode("utf-8"))


def rollback_exclude_block(exclude_path: Path, prior_content: bytes) -> None:
    """Atomically restore *exclude_path* to *prior_content*.

    Called during install rollback (AC21): if a write step fails after
    the exclude block was already written, this function restores the
    file to its pre-write state. Deleting installed files before calling
    this function is mandatory to avoid a transient window where the
    files are git-visible and non-excluded.

    Args:
        exclude_path: absolute path to the ``info/exclude`` file.
        prior_content: the raw bytes of the file before any modification.
    """
    _write_atomically(exclude_path, prior_content)


def snapshot_exclude(exclude_path: Path) -> bytes:
    """Return the current raw bytes of *exclude_path*, or ``b""`` if absent.

    Call before any write to capture the rollback snapshot (AC21 step 1).

    Args:
        exclude_path: absolute path to the ``info/exclude`` file.

    Returns:
        Current file bytes, or empty bytes if the file does not exist.
    """
    if exclude_path.exists():
        return exclude_path.read_bytes()
    return b""


def get_exclude_path(repo_root: Path) -> Path:
    """Return the absolute path to the ``info/exclude`` file for *repo_root*.

    Uses ``git rev-parse --git-path info/exclude`` so both primary and
    linked worktrees resolve to the shared common-dir ``info/exclude``
    (the file that actually gates git's ignore logic for this clone).

    Args:
        repo_root: the repository root to query.

    Returns:
        Absolute path to the ``info/exclude`` file; the file may not
        exist yet (it is created on first write by
        :func:`write_exclude_block`).
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-path", "info/exclude"],
        capture_output=True,
        text=True,
    )
    raw = result.stdout.strip()
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()
