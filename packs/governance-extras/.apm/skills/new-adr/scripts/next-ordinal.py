#!/usr/bin/env python3
"""Print the next 4-digit ordinal for a numbered-docs directory.

Usage: python3 next-ordinal.py <dir>          # print the next free ordinal
       python3 next-ordinal.py --check <dir>  # report ordinals used more than once

`--check` exits non-zero when two records share an ordinal, and also when the
directory cannot be inspected at all — a missing path, an unreadable directory,
an entry that cannot be classified, or a record-shaped symlink. Reporting
"clean" for a directory it never read would make the check worse than useless,
so the two answers are kept distinct. A companion never counts as a record: a
`NNNN-notes/` directory and a `NNNN-<slug>-research.md` sibling share their
record's ordinal by design.

Scans <dir> for filenames whose prefix is a run of 4 or more digits
terminated by `-` or `.` (e.g. `0042-foo.md`, `00099-bar.md`), parses
the digit run as an integer, and unions them with records in the default
`origin` branch when its Git metadata is available. It prints (max + 1)
zero-padded to 4 digits. Prints `0001` if the directory is missing or
contains no matching entries.

The match is strict on purpose: bare `0042.md` counts, `README.md`
does not, and `12345-foo.md` parses as 12345 (not 1234) so 5-digit
prefixes don't silently collide with 4-digit ones.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_PREFIX = re.compile(r"^(\d{4,})[-.]")
_GIT_TIMEOUT_SECONDS = 5
_GIT_REDIRECT_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
_ORIGIN_REMOTE_REF_PREFIX = "refs/remotes/origin/"


def _record_ordinal(entry: Path) -> int | None:
    """Return an entry's ordinal when its name has a record-shaped prefix."""
    if entry.name.endswith("-research.md"):
        return None
    match = _PREFIX.match(entry.name)
    return int(match.group(1)) if match else None


def _git_output(directory: Path, arguments: list[str]) -> str | None:
    """Return successful Git output without letting Git failures escape."""
    environment = os.environ.copy()
    for variable in _GIT_REDIRECT_VARIABLES:
        environment.pop(variable, None)
    try:
        result = subprocess.run(
            ["git", "--literal-pathspecs", *arguments],
            cwd=directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            shell=False,
            text=True,
            encoding="utf-8",
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None
    return result.stdout


def _remote_ordinals(directory: Path) -> set[int]:
    """Return record ordinals from the checked-out repository's default remote."""
    repository_root = _git_output(directory, ["rev-parse", "--show-toplevel"])
    if repository_root is None:
        return set()

    remote_ref = _git_output(
        directory, ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"]
    )
    if remote_ref is None:
        return set()
    ref = remote_ref.strip()
    if (
        not ref.startswith(_ORIGIN_REMOTE_REF_PREFIX)
        or ref == _ORIGIN_REMOTE_REF_PREFIX
    ):
        return set()

    try:
        relative_directory = directory.resolve().relative_to(
            Path(repository_root.strip()).resolve()
        )
    except (OSError, ValueError):
        return set()
    pathspec = (
        f"{relative_directory.as_posix()}/" if relative_directory.parts else "."
    )
    # Run from the repository root, not the target directory: Git resolves a
    # pathspec relative to the current directory, so a root-relative pathspec
    # issued from inside the directory looks for it nested under itself and
    # quietly matches nothing.
    names = _git_output(
        Path(repository_root.strip()), ["ls-tree", "--name-only", ref, "--", pathspec]
    )
    if names is None:
        return set()

    return {
        int(match.group(1))
        for name in names.splitlines()
        if (match := _PREFIX.match(Path(name).name))
    }


def duplicate_ordinals(dirpath: str | Path) -> dict[int, list[str]]:
    """Return duplicate record ordinals, refusing incomplete directory scans."""
    directory = Path(dirpath)
    if not directory.exists():
        raise ValueError(f"directory does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"not a directory: {directory}")

    records: dict[int, list[str]] = {}
    try:
        entries = list(directory.iterdir())
    except OSError as error:
        raise OSError(f"cannot enumerate directory {directory}: {error}") from error

    for entry in entries:
        ordinal = _record_ordinal(entry)
        if ordinal is None:
            continue
        try:
            if entry.is_symlink():
                raise ValueError(f"record-looking symlink: {entry}")
            if not entry.is_file():
                continue
        except OSError as error:
            raise OSError(f"cannot classify entry {entry}: {error}") from error
        records.setdefault(ordinal, []).append(entry.name)

    return {
        ordinal: sorted(names)
        for ordinal, names in records.items()
        if len(names) > 1
    }


def next_ordinal(dirpath: str) -> int:
    p = Path(dirpath)
    if not p.is_dir():
        return 1
    nums = _remote_ordinals(p)
    for name in (entry.name for entry in p.iterdir()):
        m = _PREFIX.match(name)
        if m:
            nums.add(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def main(argv: list[str] | None = None) -> int:
    """Run the ordinal allocator or the duplicate-ordinal check."""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report duplicate record ordinals")
    parser.add_argument("dir", nargs="?", default=".")
    args = parser.parse_args(argv)

    if not args.check:
        print(f"{next_ordinal(args.dir):04d}")
        return 0

    try:
        duplicates = duplicate_ordinals(args.dir)
    except (OSError, ValueError) as error:
        print(f"could not inspect {args.dir}: {error}", file=sys.stderr)
        return 1

    # Sorted because directory iteration order is unspecified and varies by
    # filesystem: an unsorted report changes line order between machines.
    for ordinal, names in sorted(duplicates.items()):
        print(f"duplicate ordinal {ordinal:04d}: {', '.join(names)}", file=sys.stderr)
    return 1 if duplicates else 0


if __name__ == "__main__":
    raise SystemExit(main())
