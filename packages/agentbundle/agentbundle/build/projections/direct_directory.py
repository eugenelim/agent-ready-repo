"""Shared helpers for `direct-directory` skill projections.

Two things live here, both shared by every direct-directory adapter:

**The orphan sweep.** After every multi-pack `project_packs(...)` call it
removes child directories of the projected skill target whose names are not in
the union of source skill names across the call's pack list. Bound to the
`skill` primitive only — other `direct-directory` projections opt in explicitly
via their adapter's `project_packs`.

**The copytree symlink policy.** Six adapters project a skill directory with
`shutil.copytree`, and each carried its own ignore callback. They had drifted
into two policies: four dropped every symlink, two dropped only symlinks with
*absolute* targets and preserved relative ones as "intra-skill
cross-references".

The permissive policy had a hole. Its docstring said "absolute symlinks always
escape the tree" — true, and incomplete: a relative symlink escapes just as
well, and `../../../../etc/passwd` needs no leading slash. Preserved into the
projection, it is then dereferenced by the install walker's `read_bytes()`,
embedding out-of-tree content in an adopter's tree.

The capability it protected turned out to be unusable: no symlink exists
anywhere under `packs/` (measured: zero), and `lint_packs.py` rejects any pack
that ships one — so a first-party pack cannot introduce one, leaving the
untrusted-catalogue install path as the only way a symlink arrives, which is
exactly where preserving it is the hazard. One strict policy, stated once.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink and `__pycache__`.

    Drops **nested** symlinks during the copy so none is reproduced in the
    output tree. A caller's top-level `is_symlink()` check covers only the
    skill root; this covers the subtree. Build runs against trusted `packs/`;
    this is the install-from-untrusted-catalogue defense.

    `__pycache__` is excluded because `.pyc` files embed absolute source paths
    and can never be byte-identical across machines.

    With this in place `copytree`'s `symlinks=` argument is moot — no symlink
    survives the filter either way.
    """
    base = Path(directory)
    return {
        name for name in names
        if name == "__pycache__" or (base / name).is_symlink()
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
