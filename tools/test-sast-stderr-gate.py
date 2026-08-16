#!/usr/bin/env python3
"""Self-test for tools/run-bandit-gate.py — the stderr-fails-the-gate rule.

ADR-0084 makes any Bandit stderr line a `make sast` failure. That rule is
invisible on a healthy repo: a clean scan and a scan whose diagnostics were
accidentally dropped look identical. Without this file the gate would be
exactly the shape ADR-0084 § Context refuses — silent when it works and silent
when it has been broken into a no-op — which is why tools/test-audit-requirements.py
and tools/test-semgrep-argv-boundary.py already sit in the same recipe.

Drives the wrapper against a stub `bandit` placed first on PATH, so the
assertions are about the wrapper's contract and never about the repo's current
findings:

  1. Clean scan (exit 0, no stderr)                       -> gate exits 0.
  2. Clean scan carrying ONE stderr diagnostic (exit 0)   -> gate exits 1.
     The load-bearing case: bandit itself says "fine", the wrapper says no.
  3. Findings (exit 1, no stderr)                         -> gate exits 1,
     i.e. the wrapper still passes bandit's own verdict through.
  4. Whitespace-only stderr                               -> gate exits 0,
     so a stray newline cannot red the build.
  5. No scan roots                                        -> usage error, 2.

Run: python3 tools/test-sast-stderr-gate.py
Exit 0 = all pass; non-zero = at least one failure.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404  # list argv, no shell; argv[0] is sys.executable
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE = REPO_ROOT / "tools" / "run-bandit-gate.py"

STUB = """#!/usr/bin/env python3
import sys
err = {stderr!r}
if err:
    sys.stderr.write(err)
sys.stdout.write("stub bandit ran\\n")
sys.exit({code})
"""


def _run_gate(stderr_text: str, code: int, roots: list[str]) -> int:
    """Run the gate with a stub `bandit` that emits *stderr_text* and *code*."""
    with tempfile.TemporaryDirectory() as tmp:
        shim = Path(tmp) / "bandit"
        shim.write_text(STUB.format(stderr=stderr_text, code=code), encoding="utf-8")
        shim.chmod(0o700)
        env = dict(os.environ, PATH=f"{tmp}{os.pathsep}{os.environ.get('PATH', '')}")
        proc = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(GATE), *roots],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        return proc.returncode


CASES = [
    ("clean scan passes", "", 0, ["tools"], 0),
    (
        "one stderr diagnostic fails the gate even though bandit exited 0",
        "[manager]\tWARNING\tTest in comment: shell is not a test name or id, ignoring\n",
        0,
        ["tools"],
        1,
    ),
    ("findings still fail, with bandit's own status", "", 1, ["tools"], 1),
    ("whitespace-only stderr does not fail the gate", "\n  \n", 0, ["tools"], 0),
    ("no scan roots is a usage error", "", 0, [], 2),
]


def main() -> int:
    if not GATE.is_file():
        print(f"test-sast-stderr-gate: missing {GATE}", file=sys.stderr)
        return 1

    failures = 0
    for name, stderr_text, code, roots, expected in CASES:
        got = _run_gate(stderr_text, code, roots)
        if got == expected:
            print(f"  ok   {name}")
        else:
            print(f"  FAIL {name}: expected exit {expected}, got {got}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"\ntest-sast-stderr-gate: {failures} failure(s).", file=sys.stderr)
        return 1
    print(f"\ntest-sast-stderr-gate: all {len(CASES)} cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
