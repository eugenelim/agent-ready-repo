#!/usr/bin/env python3
"""Install the pull-request template into this repository's forge paths.

Safe to re-run: an existing template is kept, never replaced. Reads and writes
must resolve inside the repository, so a symlink or junction that redirects a
path out of it is refused. An existing destination symlink is preserved rather
than refused: nothing is written there, and pointing a template at a shared
team location is the adopter's business.

Run from the repository root. Exits non-zero if any destination failed.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# The asset is this script's sibling: `<adapter-root>/work-loop/assets/`. The
# path the user invoked already identifies the adapter, so scanning for one was
# redundant — and let a stale install under another root refuse a valid call.
ASSET = Path(__file__).resolve().parent.parent / "assets" / "pull-request-template.md"
DESTINATIONS = (
    Path(".github/pull_request_template.md"),
    Path(".gitlab/merge_request_templates/Default.md"),
)


class Refusal(Exception):
    """A stated reason the install did not proceed."""


def escapes_root(path: Path, root: Path) -> bool:
    """True when `path` does not resolve to somewhere under `root`.

    Resolution, not a symlink walk. `Path.is_symlink()` is false for a Windows
    directory junction, so a junction at any ancestor would pass a walk while
    still redirecting the read or the write. `resolve()` follows symlinks AND
    reparse points on every platform, so comparing the resolved path against the
    resolved root catches both without reaching for platform APIs.

    The nearest existing ancestor is resolved when the path itself is absent:
    a destination that does not exist yet still has a parent that can redirect.
    """
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    try:
        resolved = probe.resolve(strict=False)
    except OSError:
        return True
    return not resolved.is_relative_to(root)


def find_asset(root: Path) -> Path:
    """This script's sibling asset, confined to the repository."""
    if not ASSET.is_file():
        raise Refusal(f"the template is missing at {ASSET} — reinstall the core pack")
    if escapes_root(ASSET, root):
        raise Refusal(f"refusing {ASSET}: its path leaves the repository")
    return ASSET


def _show(path: Path, root: Path) -> str:
    """A repository-relative path, because an absolute one is noise in a report."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def install_one(src: Path, dest: Path, root: Path) -> bool:
    """Install one destination. Returns True on success, False on refusal."""
    # Keep BEFORE confining. An existing destination is never written, so where
    # it points is the adopter's business — a template symlinked to a shared
    # team location is a legitimate setup, and refusing it would fail an install
    # that touches nothing. `is_symlink` as well as `exists`: the latter is
    # False for a dangling link, which is still a path this repository owns.
    # `is_file()` follows a symlink, so a link to a real file is kept. A dangling
    # link is kept too: nothing is written, and the adopter owns that path.
    if dest.is_file() or (dest.is_symlink() and not dest.exists()):
        print(f"keeping your existing {_show(dest, root)}")
        return True
    if dest.exists() or dest.is_symlink():
        # A directory or special file — reached directly or through a link — is
        # not a template the forge can read, and reporting it as kept would
        # claim an install that never happened.
        print(f"refusing {_show(dest, root)}: it exists and is not a file",
              file=sys.stderr)
        return False
    # Only a write needs confinement, and only the parent can redirect it.
    if escapes_root(dest.parent, root):
        print(f"refusing {_show(dest, root)}: its path leaves the repository",
              file=sys.stderr)
        return False
    # Write a sibling temp file and publish by rename, so a copy that fails
    # part-way leaves no truncated destination for the keep branch above to
    # mistake for the adopter's own template on a later run.
    #
    # `mkstemp`, not a predictable `.partial` name: it creates with O_EXCL and a
    # random suffix, so a path pre-created as a symlink cannot be hit and cannot
    # be followed. A fixed name was exploitable — bytes landed outside the
    # repository while the install reported success.
    tmp: Path | None = None
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp_name = tempfile.mkstemp(dir=dest.parent, prefix=".pr-template-")
        tmp = Path(tmp_name)
        with os.fdopen(handle, "wb") as out, src.open("rb") as source:
            shutil.copyfileobj(source, out)
        # `mkstemp` creates 0600 and `replace` preserves it, so without this the
        # installed template is owner-only while the asset it came from is
        # world-readable. Copy the source's mode, not a hardcoded one.
        shutil.copymode(src, tmp)
        tmp.replace(dest)
        tmp = None
    except OSError as exc:
        # The cleanup must not raise: an exception here would crash the handler
        # and skip every remaining destination.
        if tmp is not None:
            with contextlib.suppress(OSError):
                tmp.unlink()
        print(f"could not install {_show(dest, root)}: {exc.strerror}", file=sys.stderr)
        return False
    print(f"installed {_show(dest, root)}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        src = find_asset(root)
    except Refusal as exc:
        print(str(exc), file=sys.stderr)
        return 1

    failed = False
    for destination in DESTINATIONS:
        if not install_one(src, root / destination, root):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
