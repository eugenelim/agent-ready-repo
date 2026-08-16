#!/usr/bin/env python3
"""Run Bandit as a gate, treating its stderr as a failure (ADR-0084).

Bandit's exit code answers "did I find anything?". It does not answer "was my
own input sound?" — that goes to stderr and is then discarded by a plain
`bandit …` recipe line. Under `-q` that stderr carries exactly the diagnostics
a suppression author needs to see:

  * ``Test in comment: <word> is not a test name or id`` — a suppression whose
    reason leaked into the test-id list. The words that *do* resolve join the
    suppression; a word colliding with a real test name widens it silently.
  * ``nosec encountered (BNNN), but no failed test`` — a suppression covering a
    statement the test never fires on, i.e. stale or misplaced.
  * file-level read/parse errors — a file that was never actually scanned.

None of those move the exit code, so this wrapper does: any stderr output fails
the gate. Findings still go to stdout and still set the exit status.

Run: python3 tools/run-bandit-gate.py <scan-root> [<scan-root> …]
Exit 0 = clean, 1 = findings or diagnostics, 2 = usage/tool error.
Proven by tools/test-sast-stderr-gate.py.
"""

from __future__ import annotations

import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "bandit"
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = "bandit.yaml"

# The floor lives here and in bandit.yaml's header comment, not on the recipe
# line, so the two cannot drift apart silently.
FLOOR = ["--severity-level", "medium", "--confidence-level", "medium", "-q"]

HINT = (
    "make sast: bandit wrote diagnostics to stderr — that is a gate failure, not\n"
    "make sast: chatter. A `# nosec` bandit cannot parse can suppress more than\n"
    "make sast: its author wrote. See ADR-0084 and bandit.yaml's header comment."
)


def main(argv: list[str]) -> int:
    roots = argv[1:]
    if not roots:
        print(f"usage: {Path(argv[0]).name} <scan-root> [<scan-root> ...]", file=sys.stderr)
        return 2

    cmd = ["bandit", "-r", *roots, "-c", CONFIG, *FLOOR]
    print(" ".join(cmd))
    try:
        # stdout inherited so findings stream as they would from a bare recipe
        # line; only stderr is captured, because only stderr is being judged.
        proc = subprocess.run(  # nosec B603  # list argv, no shell; roots are the Makefile's SAST_DIRS
            cmd,
            cwd=REPO_ROOT,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"run-bandit-gate: could not run bandit: {exc}", file=sys.stderr)
        return 2

    if proc.stderr.strip():
        sys.stderr.write(proc.stderr if proc.stderr.endswith("\n") else proc.stderr + "\n")
        print(HINT, file=sys.stderr)
        return 1

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
