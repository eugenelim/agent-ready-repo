"""Shared helpers for `direct-directory` skill projections.

After every multi-pack `project_packs(...)` call, the orphan sweep
removes child directories of the projected skill target whose names
are not in the union of source skill names across the call's pack list.

Bound to the `skill` primitive only — other `direct-directory`
projections opt in explicitly via their adapter's `project_packs`.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def ignore_absolute_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: drop absolute-target symlinks and
    `__pycache__`, and PRESERVE relative ones as symlinks.

    One definition for all six direct-directory adapters. They previously
    carried six private copies that had drifted into two policies — four
    dropping every symlink, two dropping only absolute targets — which is what
    six copies of one rule does.

    The surviving policy is pass-through, because
    `docs/specs/codex-native-skills/spec.md` states it as the invariant:
    "the symlink-pass-through is the path-traversal-safety invariant; never
    resolve a symlink to its target at projection time". Resolving is what
    materialises a target's bytes into the output; preserving the link does not,
    and `render._collect_tree` refuses to read through a link, so a preserved
    link cannot become a file on an adopter's disk either.

    Absolute targets are still dropped: they always escape the tree and carry no
    meaning once the tree is copied elsewhere. A relative link survives as a
    link — including one that traverses upward, which is safe for the same
    reason the invariant gives, and visible as a link to anything that inspects
    the output.

    `__pycache__` is excluded because `.pyc` files embed absolute source paths
    and can never be byte-identical across machines.
    """
    base = Path(directory)
    return {
        name for name in names
        if name == "__pycache__"
        or ((base / name).is_symlink() and (base / name).readlink().is_absolute())
    }


def sweep_orphans(target_dir: Path, expected_names: set[str]) -> None:
    if not target_dir.exists():
        return
    for entry in target_dir.iterdir():
        if entry.is_symlink():
            if entry.name not in expected_names:
                # Destructive operation — leave a breadcrumb so adopters
                # can trace what disappeared without bisecting commits.
                print(
                    f"sweep_orphans: removed orphan symlink {entry} "
                    f"(not in expected source-skill names)",
                    file=sys.stderr,
                )
                entry.unlink()
            continue
        if not entry.is_dir():
            continue
        if entry.name not in expected_names:
            print(
                f"sweep_orphans: removed orphan directory {entry} "
                f"(not in expected source-skill names)",
                file=sys.stderr,
            )
            shutil.rmtree(entry)
