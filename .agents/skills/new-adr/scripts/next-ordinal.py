#!/usr/bin/env python3
"""Print the next 4-digit ordinal for a numbered-docs directory.

Usage: python3 next-ordinal.py <dir>

Scans <dir> for filenames whose prefix is a run of 4 or more digits
terminated by `-` or `.` (e.g. `0042-foo.md`, `00099-bar.md`), parses
the digit run as an integer, prints (max + 1) zero-padded to 4 digits.
Prints `0001` if the directory is missing or contains no matching
entries.

The match is strict on purpose: bare `0042.md` counts, `README.md`
does not, and `12345-foo.md` parses as 12345 (not 1234) so 5-digit
prefixes don't silently collide with 4-digit ones.
"""
import os
import re
import sys

_PREFIX = re.compile(r"^(\d{4,})[-.]")


def next_ordinal(dirpath: str) -> int:
    if not os.path.isdir(dirpath):
        return 1
    nums = []
    for name in os.listdir(dirpath):
        m = _PREFIX.match(name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"{next_ordinal(target):04d}")
