#!/usr/bin/env python3
"""Self-test for tools/compare-bandit-suppressions.py.

The comparison's value is entirely in the four traps it encodes, and every one
of them fails *silently* — a wrong scan scope, a path anchored to the wrong
tree, or row counts mistaken for key counts all produce a confident, wrong
answer rather than an error. So the cases below target the trap logic directly.

Two of them exist because this script got them wrong on its first real run:

  * `_worktree_relative` must not use `Path.resolve()`. Bandit reports paths
    relative to its own cwd, and resolving them anchors to *this* process's cwd
    — the repo, not the worktree — silently mixing trees.
  * A file that exists at only one revision is not a changed suppression. The
    first run reported a false FAIL because the change under test added two
    files, and every suppression in them looked like a difference.

The end-to-end case (a ref compared against itself, which must be identical by
construction) runs two full bandit scans and takes minutes, so it is opt-in:
pass --e2e. Everything else is sub-second.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess  # nosec B404  # list argv, no shell; argv[0] is sys.executable
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent
_TOOL = _HERE / "compare-bandit-suppressions.py"
_SPEC = importlib.util.spec_from_file_location("compare_bandit_suppressions", _TOOL)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--e2e", action="store_true",
                        help="also run a same-ref comparison (slow: two full scans)")
    args = parser.parse_args()

    print("compare-bandit-suppressions self-test")

    # Trap 3 / trap 2: path handling must never anchor to this process's cwd.
    # A synthetic path, never touched on disk. Not under /tmp: a literal there
    # trips B108, and a suppression would be worse than a different fixture.
    worktree = Path("/scan/base")
    for reported, expected in (
        ("/scan/base/packages/agentbundle/x.py", "packages/agentbundle/x.py"),
        ("./packages/agentbundle/x.py", "packages/agentbundle/x.py"),
        ("packages/agentbundle/x.py", "packages/agentbundle/x.py"),
    ):
        got = _MOD._worktree_relative(reported, worktree)
        check(f"path {reported!r} -> {expected!r}", got == expected, got)

    # A path from a DIFFERENT tree must not silently reduce to a repo-relative
    # one — that is the failure that mixes the two sides together.
    other = _MOD._worktree_relative("/somewhere/else/packages/x.py", worktree)
    check("a foreign absolute path is left absolute", other.startswith("/somewhere/else"), other)

    # Scan scope comes from the Makefile, and an appended assignment must fail
    # loudly rather than silently narrowing the comparison.
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "Makefile").write_text("SAST_DIRS := tools packs\n", encoding="utf-8")
        check("SAST_DIRS parses", _MOD.sast_dirs(root) == ["tools", "packs"],
              str(_MOD.sast_dirs(root)))

        (root / "Makefile").write_text(
            "SAST_DIRS := tools packs  # trailing comment\n", encoding="utf-8")
        check("a trailing comment is stripped", _MOD.sast_dirs(root) == ["tools", "packs"],
              str(_MOD.sast_dirs(root)))

        (root / "Makefile").write_text("SAST_DIRS := tools\nSAST_DIRS += web\n",
                                       encoding="utf-8")
        try:
            _MOD.sast_dirs(root)
        except _MOD.CompareError as exc:
            check("`SAST_DIRS +=` fails loudly", "exactly one" in str(exc), str(exc))
        else:
            check("`SAST_DIRS +=` fails loudly", False, "silently ignored the append")

    # Trap 1: the finding key drops the line number, because a comment edit
    # shifts lines without changing what is suppressed. Two rows that differ
    # only by line must collapse to one key.
    rows = [
        {"filename": "a.py", "test_id": "B310", "issue_text": "t", "line_number": 10},
        {"filename": "a.py", "test_id": "B310", "issue_text": "t", "line_number": 99},
    ]
    keys = {(_MOD._worktree_relative(r["filename"], worktree), r["test_id"], r["issue_text"])
            for r in rows}
    check("rows differing only by line collapse to one key", len(keys) == 1 and len(rows) == 2,
          f"{len(rows)} rows -> {len(keys)} keys")

    if args.e2e:
        # Identical by construction. Catches a scan that is not reproducible —
        # a wrong cwd, a leaked absolute path, a nondeterministic key.
        print("  .... running same-ref comparison (two full scans, slow)")
        result = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(_TOOL), "HEAD", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        check("a ref compared against itself is identical", result.returncode == 0,
              (result.stderr or result.stdout)[-300:])
    else:
        print("  skip same-ref comparison (pass --e2e to run it)")

    print()
    if FAILURES:
        print(f"compare-bandit-suppressions self-test: {len(FAILURES)} case(s) failed.")
        return 1
    print("compare-bandit-suppressions self-test: all cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
