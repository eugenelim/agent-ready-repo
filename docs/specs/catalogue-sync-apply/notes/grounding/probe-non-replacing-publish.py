#!/usr/bin/env python3
"""Probe: does a link-based publish deliver what the companion write claims?

The criterion claims three properties at once — never replaces an existing
destination, stays atomic so no partial artifact is observable, and lands at
the staged file's permission bits. The obvious alternative, opening the
destination `O_CREAT | O_EXCL` and writing into it, delivers the first and
loses the other two.

Checks each property, and each occupant kind separately: a criterion that
says "never replaces" is satisfied by a mechanism that refuses a regular file
and silently follows a symlink.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-non-replacing-publish.py
"""
from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages" / "agentbundle"))

from agentbundle.catalogue_tooling.file_safety import (  # noqa: E402
    UnsafeContentError,
    read_confined_regular_file,
)


def stage(directory: Path, content: bytes = b"upstream bytes\n") -> Path:
    """Stage exactly as the replacing mode does: mkstemp in the target dir."""
    handle, name = tempfile.mkstemp(prefix="x.", suffix=".tmp", dir=str(directory))
    with os.fdopen(handle, "wb") as stream:
        stream.write(content)
    return Path(name)


OCCUPANTS = [
    ("regular file", lambda p: p.write_bytes(b"adopter work\n")),
    ("empty file", lambda p: p.touch()),
    ("symlink", lambda p: p.symlink_to("/etc/passwd")),
    ("dangling symlink", lambda p: p.symlink_to(p.parent / "absent")),
    ("directory", lambda p: p.mkdir()),
]


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        print("1. never replaces — per occupant kind")
        for kind, setup in OCCUPANTS:
            dest = root / f"occ-{kind.replace(' ', '-')}.upstream.md"
            setup(dest)
            src = stage(root)
            try:
                os.link(src, dest)
                outcome, ok = "LINKED — would clobber", False
            except FileExistsError:
                outcome, ok = "refused (FileExistsError)", True
            except OSError as exc:
                outcome, ok = f"refused (errno {exc.errno})", True
            failures += not ok
            print(f"   {kind:>17}: {outcome}")
            src.unlink(missing_ok=True)

        print("\n2. lands at the staged file's permission bits")
        dest = root / "fresh.upstream.md"
        src = stage(root)
        staged_mode = stat.S_IMODE(src.stat().st_mode)
        os.link(src, dest)
        dest_mode = stat.S_IMODE(dest.stat().st_mode)
        src.unlink()
        agree = staged_mode == dest_mode
        failures += not agree
        print(f"   staged {oct(staged_mode)} -> published {oct(dest_mode)}: "
              f"{'agree' if agree else 'DIVERGE'}")

        print("\n3. the post-publish state — the half a happy-path probe misses")
        dest = root / "published.upstream.md"
        src = stage(root)
        os.link(src, dest)
        linked_nlink = dest.stat().st_nlink
        residue = src.exists()
        try:
            read_confined_regular_file(root, dest)
            readable_before = "OK"
        except UnsafeContentError as exc:
            readable_before = f"REFUSED — {exc}"
        src.unlink()
        settled_nlink = dest.stat().st_nlink
        try:
            read_confined_regular_file(root, dest)
            readable_after = "OK"
        except UnsafeContentError as exc:
            readable_after = f"REFUSED — {exc}"
        print(f"   immediately after the link: st_nlink={linked_nlink}, "
              f"staged residue present={residue}")
        print(f"     the confined reader this feature must use says: {readable_before}")
        print(f"   after unlinking the staged name: st_nlink={settled_nlink}")
        print(f"     the confined reader says: {readable_after}")
        failures += linked_nlink != 1
        print("   => a link does not consume the staged name, unlike a rename.")
        print("      Until it is unlinked the published companion is unreadable")
        print("      by the tool's own helpers, and the residue carries the full")
        print("      source bytes at a path stale removal can never reclaim.")

        print("\n4. same filesystem, by construction")
        nested = root / "sub"
        nested.mkdir()
        target = nested / "y.upstream.md"
        src = stage(nested)
        same = src.parent == target.parent and src.stat().st_dev == nested.stat().st_dev
        failures += not same
        src.unlink()
        print(f"   staging happens in the destination's own directory: {same}")
        print("   so the cross-device case a link would fail on cannot arise")

    print(f"\nproperties not delivered as specified: {failures}")
    print(
        "two residuals the criterion must carry: os.link reports EEXIST for an "
        "occupant but also EPERM/EOPNOTSUPP where the filesystem has no hard "
        "links, so reading any link failure as occupancy misreports a dropped "
        "companion as a preserved one; and the publish must unlink the staged "
        "name, because until it does the destination is a hard link the "
        "confined reader refuses"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
