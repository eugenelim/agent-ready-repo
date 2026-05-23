"""``agentbundle uninstall`` — remove a pack's Tier-1 files from the adopter tree.

Algorithm:
  1. Load ``.agent-ready-state.toml`` from ``args.root``.
     Exit non-zero with stderr if the pack is not in state.
  2. For each file recorded under ``[pack.<name>.files]``:
     - Compute the on-disk SHA.
     - If it matches the state-recorded SHA (Tier-1) → ``os.remove``.
     - If it differs (or file is absent) → Tier-2 → warn on stderr and keep.
  3. Best-effort: remove empty parent directories left behind by removals.
  4. Save the updated state file with ``[pack.<name>]`` table dropped.
  5. Print summary to stdout: N removed, M kept.
  6. Exit 0.

Tier-3 files (paths not recorded in the pack's state table) are never touched.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle uninstall``.

    Args:
        args.pack  — name of the pack to uninstall (required).
        args.root  — repo root directory (default '.').

    Returns 0 on success, non-zero on error.
    """
    from agentbundle.config import ConfigError, dump_state, load_state
    from agentbundle import safety

    pack_name: str = args.pack
    root = Path(args.root).resolve()
    state_path = root / ".agent-ready-state.toml"

    # ── Step 1: Load state; verify pack is installed ──────────────────────────
    try:
        state = load_state(state_path)
    except ConfigError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

    if pack_name not in state.packs:
        print(f"uninstall: pack {pack_name!r} not installed", file=sys.stderr)
        return 1

    pack_state = state.packs[pack_name]

    # ── Step 2: Walk the pack's recorded files ────────────────────────────────
    removed: list[str] = []
    kept: list[str] = []

    for relpath, entry in sorted(pack_state.files.items()):
        on_disk = root / relpath
        recorded_sha = entry.get("sha") if isinstance(entry, dict) else None

        # If the file is absent on disk, treat as already gone (Tier-2 edge
        # case: the adopter deleted it manually). Do not error — just skip.
        if not on_disk.exists():
            # Not present → nothing to remove; also not an adopter edit we
            # need to preserve. Skip silently.
            continue

        # Compute on-disk SHA and compare against the recorded value.
        on_disk_sha = safety.sha256_file(on_disk)
        if recorded_sha and on_disk_sha == recorded_sha:
            # Tier-1: the bundle owns this file — safe to remove.
            try:
                os.remove(on_disk)
            except OSError as exc:
                print(
                    f"uninstall: could not remove {relpath}: {exc}",
                    file=sys.stderr,
                )
                return 1
            removed.append(relpath)
        else:
            # Tier-2: adopter-edited (or no recorded SHA) — preserve with warning.
            print(
                f"uninstall: keeping adopter-edited file: {relpath}",
                file=sys.stderr,
            )
            kept.append(relpath)

    # ── Step 3: Best-effort cleanup of empty parent directories ──────────────
    _prune_empty_parents(root, removed)

    # ── Step 4: Remove the pack's table from state and persist ────────────────
    del state.packs[pack_name]
    serialised = dump_state(state)
    try:
        safety.write_jailed(root, ".agent-ready-state.toml", serialised)
    except safety.PathJailError as exc:
        print(f"uninstall: {exc}", file=sys.stderr)
        return 1

    # ── Step 5: Summary ───────────────────────────────────────────────────────
    print(f"uninstall: {len(removed)} removed, {len(kept)} kept")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prune_empty_parents(root: Path, removed_relpaths: list[str]) -> None:
    """Remove empty directories left behind after file deletions.

    Works bottom-up: for each removed file, walk its parents upward until
    reaching ``root`` or a non-empty directory. Ignores all errors — this is
    best-effort housekeeping.
    """
    # Collect unique parent directories in deepest-first order.
    dirs_to_check: set[Path] = set()
    for relpath in removed_relpaths:
        parent = (root / relpath).parent
        while parent != root and parent != parent.parent:
            dirs_to_check.add(parent)
            parent = parent.parent

    # Sort deepest first (longest path first) so we remove children before
    # parents — avoids trying to remove a directory that still has children.
    for d in sorted(dirs_to_check, key=lambda p: len(p.parts), reverse=True):
        try:
            d.rmdir()  # Only succeeds if the directory is empty.
        except OSError:
            pass  # Not empty or other error — skip silently.
