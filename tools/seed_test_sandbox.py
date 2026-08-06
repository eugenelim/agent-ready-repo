#!/usr/bin/env python3
"""Seed a sandbox copy of the working tree for `tools/test-pre-pr.sh`.

Copies the set the self-test has always used — `git ls-files` plus
`git ls-files --others --exclude-standard` — into `<dest>`, preserving symlinks.
The caller is responsible for `git init`-ing the result.

This runs as one process rather than the two subprocess spawns per file
(`mkdir -p` + `cp -P`) the shell loop used to do. Timings and the rationale are
in `docs/specs/test-sandbox-seed-cost/spec.md`.

Symlinks must survive as symlinks — dereferencing them is the K-0002 regression
class in `docs/knowledge/patterns.jsonl`, and it fails quietly: the sandbox still
seeds, and the self-test still passes, while `CLAUDE.md` and the deliberate
`version_gate` fixture link have silently become regular files. Rather than
check a hardcoded list that rots whenever a symlink is added, every symlink this
script copies is verified as it is copied.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=True
    ).stdout


def seed_set(root: Path) -> list[str]:
    """Tracked files plus untracked-but-not-ignored files, in git's order.

    The untracked half is load-bearing: `make build-self` writes projections
    that are untracked in a fresh checkout, and the self-host drift check inside
    `catalogue verify` fails without them. This is why the sandbox cannot be
    built with `git clone --local`, which carries committed state only.
    """
    raw = _git(root, "ls-files", "-z") + _git(
        root, "ls-files", "-z", "--others", "--exclude-standard"
    )
    # os.fsdecode, not bytes.decode: git emits raw path bytes under -z, so a
    # single non-UTF-8 filename would otherwise abort the copy part-way and
    # leave a half-seeded sandbox.
    return [os.fsdecode(p) for p in raw.split(b"\0") if p]


def seed(root: Path, dest: Path) -> tuple[int, int]:
    """Copy the seed set into `dest`. Returns (files copied, symlinks copied)."""
    made: set[Path] = set()
    copied = links = 0

    for rel in seed_set(root):
        src = root / rel
        # A *broken* symlink still needs copying, so test is_symlink() first —
        # exists() follows the link and would report False for one.
        if not src.is_symlink() and not src.exists():
            print(
                f"warn [seed]: tracked path absent from the working tree, "
                f"not seeded: {rel}",
                file=sys.stderr,
            )
            continue

        out = dest / rel
        if out.parent not in made:
            out.parent.mkdir(parents=True, exist_ok=True)
            made.add(out.parent)
        # The caller tolerates an `rm -rf` that left files behind (a GitHub-runner
        # race it retries around). `cp -P` overwrote such leftovers; the os.symlink
        # inside copy2 raises FileExistsError instead, so clear the path first.
        if out.is_symlink() or out.exists():
            out.unlink()
        # follow_symlinks=False is exactly what `cp -P` did.
        shutil.copy2(src, out, follow_symlinks=False)
        copied += 1

        if src.is_symlink():
            links += 1
            if not out.is_symlink():
                sys.exit(
                    f"FAIL [seed]: '{rel}' was dereferenced while seeding the "
                    f"sandbox\n  seeding must preserve symlinks as symlinks "
                    f"(see K-0002 in docs/knowledge/patterns.jsonl)"
                )

    return copied, links


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <dest>", file=sys.stderr)
        return 2

    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    )
    copied, links = seed(root, Path(argv[1]))
    # One line per seeding, to stderr so it stays clear of the caller's `ok`
    # lines: this is the positive evidence that symlinks survived. `links` is
    # reported, not asserted to be non-zero — on Windows without Developer Mode
    # git materialises CLAUDE.md as a regular file, so 0 is legitimate there.
    print(f"seeded {copied} files ({links} symlinks preserved)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
