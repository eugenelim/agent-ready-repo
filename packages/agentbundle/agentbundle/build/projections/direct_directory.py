"""Shared post-pass helper for `direct-directory` skill projections.

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
