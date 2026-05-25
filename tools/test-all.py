#!/usr/bin/env python3
"""Umbrella runner: every self-test in tools/. Run by hand when a
linter, hook, or loop-cohort.py changes; CI runs a subset, so this is
the local-side belt-and-braces.

Pure-stdlib Python port of test-all.sh — same alphabetical list, same
`✓`/`✖` output, same exit semantics (0 if every test passed, 1 if any
failed). Pure Python so the umbrella runs on Windows without an MSYS
shell or WSL.

Distinct from tools/hooks/pre-pr.py — that's a *gate* against the
working tree (does the diff pass the linters?); this is a *suite*
of self-tests against the linters and hooks themselves (do the
tools still do what they claim?). Both have a place; both green is
the contract.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


# Each entry: (label, argv). Order is alphabetical for stability;
# nothing in the chain depends on a particular order. New `.py`
# self-tests prefer `sys.executable` over a bare `python3` so the
# child runs with the same interpreter as the umbrella.
TESTS: list[tuple[str, list[str]]] = [
    ("lint-agent-artifacts", ["bash", "tools/test-lint-agent-artifacts.sh"]),
    ("lint-knowledge",       ["bash", "tools/test-lint-knowledge.sh"]),
    ("lint-skill-spec",      [sys.executable, "tools/test-lint-skill-spec.py"]),
    ("loop-cohort",          ["bash", "tools/test-loop-cohort.sh"]),
    ("pre-pr",               ["bash", "tools/test-pre-pr.sh"]),
    ("session-start",        ["bash", "tools/test-session-start.sh"]),
]


def main() -> int:
    os.chdir(_repo_root())
    failures = 0
    ran = 0
    for label, cmd in TESTS:
        ran += 1
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✓ {label}")
        else:
            cmd_str = " ".join(cmd)
            print(f"✖ {label} — re-run `{cmd_str}` for output", file=sys.stderr)
            failures += 1

    print()
    if failures > 0:
        print(f"test-all: {failures} of {ran} failed", file=sys.stderr)
        return 1
    print(f"test-all: {ran} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
