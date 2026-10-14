#!/usr/bin/env python3
"""Fail when a copy of the shared view stylesheet drifts from its canonical file.

The canonical file lives at
``packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css``.
Every other file named ``view-base.css`` under ``packs/*/.apm/`` is a copy that an adopting
skill carries inside its own tree, and must be byte-identical to it. A symlinked copy counts
as a difference: each skill ships real bytes.

Exit 0 when every copy matches, 1 when any differs or the canonical file is missing.
Files are read through the confinement helper, which refuses symlinks.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
AGENTBUNDLE = SOURCE_ROOT / "packages" / "agentbundle"
if str(AGENTBUNDLE) not in sys.path:
    sys.path.insert(0, str(AGENTBUNDLE))

from agentbundle.catalogue_tooling.file_safety import (  # noqa: E402
    UnsafeContentError,
    read_confined_regular_file,
)

CANONICAL = Path("packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css")
NAME = "view-base.css"


def find_copies(root: Path) -> list[Path]:
    """Return every ``view-base.css`` under ``packs/*/.apm/``, relative to *root*, sorted."""
    found = []
    for apm in sorted((root / "packs").glob("*/.apm")):
        found.extend(p.relative_to(root) for p in apm.rglob(NAME))
    return sorted(found)


def check(root: Path) -> list[str]:
    """Return one problem line per copy that differs, or for a missing canonical file."""
    try:
        expected = read_confined_regular_file(root, root / CANONICAL)
    except (UnsafeContentError, OSError):
        return [f"{CANONICAL}: canonical shared stylesheet is missing or not a regular file"]
    problems = []
    for rel in find_copies(root):
        if rel == CANONICAL:
            continue
        try:
            data = read_confined_regular_file(root, root / rel)
        except (UnsafeContentError, OSError):
            problems.append(f"{rel}: not a regular file; copy the canonical bytes instead")
            continue
        if data != expected:
            problems.append(f"{rel}: differs from {CANONICAL}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Run the parity check and report each drifted copy on stderr."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    problems = check(args.root.resolve())
    for line in problems:
        print(f"check-view-base-parity: {line}", file=sys.stderr)
    if problems:
        print(
            "check-view-base-parity: edit the canonical file and every copy in one change",
            file=sys.stderr,
        )
        return 1
    print(f"check-view-base-parity: ok ({len(find_copies(args.root.resolve()))} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
