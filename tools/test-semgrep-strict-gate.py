#!/usr/bin/env python3
"""Self-test for tools/run-semgrep-gate.py — the never-fail-in-silence rule.

The wrapper exists because `--strict --quiet` together make semgrep exit
non-zero with zero bytes on stdout and stderr. That failure is invisible on a
healthy repo: a clean scan and a scan whose diagnostics were dropped look
identical, which is the shape ADR-0084 refuses. Without this file the wrapper
would be exactly that shape itself.

Drives the wrapper against a stub `semgrep` placed first on PATH, so every
assertion is about the wrapper's contract and never about the repo's current
findings. The stub honours `--json-output=FILE` the way real semgrep does.

Asserts:
  1. Clean scan (exit 0)                          -> gate exits 0, prints nothing to stderr.
  2. `--strict` diagnostic (exit 3, errors[])     -> gate exits 3 AND names the path.
     The load-bearing case: real semgrep prints nothing here, the wrapper must.
  3. Findings (exit 1, no errors[])               -> gate exits 1 with no invented
     diagnostic; the findings already went to stdout.
  4. Non-zero with an empty errors[] (exit 2)     -> gate exits 2 and still says
     something, rather than passing the silence through.
  5. Unreadable/absent JSON report (exit 3)       -> gate exits 3 and says the
     report could not be read, rather than crashing or going quiet.
  6. No arguments                                 -> usage error, 2.
  7. Control characters in a scanner-supplied path -> escaped, so a hostile path
     cannot rewrite the surrounding log lines.
  8. Argv passthrough: every argument reaches semgrep and exactly one
     `--json-output` is added. Without this the wrapper could drop `--strict` —
     reverting the point of the gate — and cases 1-7 would all still pass.
  9. semgrep's own stdout reaches the caller, so findings still stream. Without
     this the wrapper could capture and swallow every finding, silently.

Run: python3 tools/test-semgrep-strict-gate.py
Exit 0 = all pass; non-zero = at least one failure.
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404  # list argv, no shell; argv[0] is sys.executable
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE = REPO_ROOT / "tools" / "run-semgrep-gate.py"

# Mimics real semgrep closely enough to test the contract: it writes the JSON
# report to whatever `--json-output=` names, prints nothing else, and exits with
# the code the case asked for. `write_report` False models the case where the
# file never appears.
# `argv_sink` and the stdout marker are what stop this file being theatre. Without
# them the wrapper could drop `--strict`, or capture semgrep's stdout and swallow
# every finding, and every case below would still pass.
STUB = """#!/usr/bin/env python3
import json, sys
payload = {payload!r}
write_report = {write_report!r}
argv_sink = {argv_sink!r}
target = None
for arg in sys.argv[1:]:
    if arg.startswith("--json-output="):
        target = arg.split("=", 1)[1]
with open(argv_sink, "w", encoding="utf-8") as handle:
    json.dump(sys.argv[1:], handle)
sys.stdout.write({marker!r} + "\\n")
if write_report and target:
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(payload)
sys.exit({code})
"""

# Written by the stub to stdout; the wrapper must let it through untouched.
STDOUT_MARKER = "stub-semgrep-finding-line"

PARTIAL_PARSE = json.dumps(
    {
        "results": [],
        "errors": [
            {
                "type": ["PartialParsing", []],
                "level": "warn",
                "path": "packs/core/.apm/hooks/session-start.py",
                "message": "Syntax error at line packs/core/.apm/hooks/session-start.py:2:\n `x = (` was unexpected",
            }
        ],
    }
)
NO_ERRORS = json.dumps({"results": [], "errors": []})
# A path and message carrying control characters, as a file in a fork PR could.
# The gate log is the one output this wrapper exists to make trustworthy, so an
# embedded newline or escape sequence must not rewrite the lines around it.
HOSTILE = json.dumps(
    {
        "results": [],
        "errors": [
            {
                "type": "PartialParsing",
                "level": "warn",
                "path": "packs/evil\n\x1b[2Kmake sast: all clear.py",
                "message": "Syntax error\rmake sast: all clear",
            }
        ],
    }
)


def _run_gate(payload: str, code: int, args: list[str], write_report: bool = True):
    """Run the gate with a stub `semgrep` that writes *payload* and exits *code*.

    Returns (exit code, stderr, stdout, argv the stub actually received).
    """
    with tempfile.TemporaryDirectory() as tmp:
        argv_sink = Path(tmp) / "argv.json"
        shim = Path(tmp) / "semgrep"
        shim.write_text(
            STUB.format(
                payload=payload,
                code=code,
                write_report=write_report,
                argv_sink=str(argv_sink),
                marker=STDOUT_MARKER,
            ),
            encoding="utf-8",
        )
        shim.chmod(0o700)
        env = dict(os.environ, PATH=f"{tmp}{os.pathsep}{os.environ.get('PATH', '')}")
        proc = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(GATE), *args],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        seen = json.loads(argv_sink.read_text(encoding="utf-8")) if argv_sink.is_file() else None
        return proc.returncode, proc.stderr, proc.stdout, seen


ARGS = ["--strict", "--error", "--quiet", "tools"]

# name, payload, exit code, argv, write report?, expected exit, substring required
# in stderr (None = stderr must carry no diagnostic line)
CASES = [
    ("clean scan passes quietly", NO_ERRORS, 0, ARGS, True, 0, None),
    (
        "a --strict diagnostic is printed with its path, not swallowed",
        PARTIAL_PARSE,
        3,
        ARGS,
        True,
        3,
        "packs/core/.apm/hooks/session-start.py",
    ),
    ("findings pass through without an invented diagnostic", NO_ERRORS, 1, ARGS, True, 1, None),
    (
        "non-zero with an empty errors[] still says something",
        NO_ERRORS,
        2,
        ARGS,
        True,
        2,
        "no findings and no errors",
    ),
    (
        "an unreadable JSON report is reported, not crashed on",
        "",
        3,
        ARGS,
        False,
        3,
        "could not be read",
    ),
    ("no arguments is a usage error", NO_ERRORS, 0, [], True, 2, "usage:"),
    (
        "control characters in a scanner-supplied path are escaped, not emitted",
        HOSTILE,
        3,
        ARGS,
        True,
        3,
        r"packs/evil\n\x1b[2Kmake sast: all clear.py",
    ),
]


def _check_passthrough() -> list[str]:
    """The wrapper forwards every argument and adds exactly one `--json-output`.

    This is the contract the module docstring names and the one the rest of the
    cases cannot see: with the stub ignoring argv, the wrapper could drop
    `--strict` — reverting the point of the gate — and stay green.
    """
    problems: list[str] = []
    args = ["--strict", "--error", "--quiet", "--config", "p/python", "tools"]
    _code, _stderr, _stdout, seen = _run_gate(NO_ERRORS, 0, args)
    if seen is None:
        return ["stub recorded no argv"]
    added = [a for a in seen if a.startswith("--json-output=")]
    forwarded = [a for a in seen if not a.startswith("--json-output=")]
    if forwarded != args:
        problems.append(f"forwarded argv {forwarded!r} != passed {args!r}")
    if len(added) != 1:
        problems.append(f"expected exactly one --json-output, got {added!r}")
    return problems


def _check_stdout_reaches_caller() -> list[str]:
    """semgrep's own stdout still reaches the caller.

    `--json-output` was chosen over `--json` precisely so findings keep streaming
    in text form. Capturing the child's stdout would swallow every finding while
    every exit-code case still passed.
    """
    _code, _stderr, stdout, _seen = _run_gate(NO_ERRORS, 1, ARGS)
    if STDOUT_MARKER not in stdout:
        return [f"semgrep stdout did not reach the caller: {stdout.strip()!r}"]
    return []


def main() -> int:
    if not GATE.is_file():
        print(f"test-semgrep-strict-gate: missing {GATE}", file=sys.stderr)
        return 1

    failures = 0
    for name, payload, code, args, write_report, expected, needle in CASES:
        got, stderr, _stdout, _seen = _run_gate(payload, code, args, write_report)
        problems = []
        if got != expected:
            problems.append(f"expected exit {expected}, got {got}")
        if needle is not None and needle not in stderr:
            problems.append(f"stderr did not mention {needle!r}: {stderr.strip()!r}")
        if needle is None and "run-semgrep-gate:" in stderr:
            problems.append(f"unexpected diagnostic on stderr: {stderr.strip()!r}")
        if problems:
            print(f"  FAIL {name}: {'; '.join(problems)}", file=sys.stderr)
            failures += 1
        else:
            print(f"  ok   {name}")

    for name, check in (
        ("every argument is forwarded, plus exactly one --json-output", _check_passthrough),
        ("semgrep's own stdout still reaches the caller", _check_stdout_reaches_caller),
    ):
        problems = check()
        if problems:
            print(f"  FAIL {name}: {'; '.join(problems)}", file=sys.stderr)
            failures += 1
        else:
            print(f"  ok   {name}")

    if failures:
        print(f"\ntest-semgrep-strict-gate: {failures} failure(s).", file=sys.stderr)
        return 1
    print(f"\ntest-semgrep-strict-gate: all {len(CASES) + 2} cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
