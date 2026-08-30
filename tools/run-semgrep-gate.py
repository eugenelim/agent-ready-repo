#!/usr/bin/env python3
"""Run semgrep as a gate, printing the diagnostics `--strict` fails on.

`--strict` promotes semgrep's own diagnostics — a partial parse failure, a rule
that timed out on a file — from printed-and-ignored into a non-zero exit. The
recipe also passes `--quiet`, and those two flags together produce a gate that
fails with **nothing on stdout and nothing on stderr**: measured on semgrep
1.166.0, a partial parse failure exits 3 with zero bytes on both streams, and a
per-rule timeout exits 2 with zero bytes on both. The contributor sees only
`make: *** [sast-unleased] Error 3`, on a file they very likely did not touch.

A gate that is silent when it passes and equally silent when it fails is the
shape ADR-0084 refuses, and it is why that ADR wrapped Bandit in a script rather
than adding a recipe flag. This is the same move for the same reason.

The diagnostic exists — it is just only in the JSON report. `--json-output=FILE`
writes that report to a file *without* changing what goes to stdout, so findings
still stream in their normal text form and this wrapper reads `errors[]` from
the file afterwards. Each entry carries the path, the level, the error type and
a message with line and column.

Run: python3 tools/run-semgrep-gate.py <semgrep-arg> [<semgrep-arg> …]
Every argument is passed through to `semgrep` untouched; only
`--json-output` is added. The exit code is semgrep's own.
Exit 0 = clean, 1 = findings, 2 = usage/tool error or a `--strict` rule timeout,
3 = a `--strict` parse diagnostic.
Proven by tools/test-semgrep-strict-gate.py.
"""

from __future__ import annotations

import json
import shlex
import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "semgrep"
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent

HINT = (
    "run-semgrep-gate: semgrep exited non-zero because of --strict. The entries\n"
    "run-semgrep-gate: above are its own diagnostics, not findings in your code: a\n"
    "run-semgrep-gate: target it could not fully parse, or a rule that exceeded its\n"
    "run-semgrep-gate: per-file time budget. Fix the target, or scope the rule in\n"
    "run-semgrep-gate: SEMGREP_EXCLUDE with a comment saying what that gives up."
)


def _safe(text: object) -> str:
    """Render scanner-supplied text so it cannot garble the gate log.

    `path` and `message` derive from files a fork PR controls, and this line is
    the one output the gate exists to make trustworthy. Escaping keeps an
    embedded control character, ANSI sequence or newline from rewriting or
    hiding the surrounding lines.
    """
    return str(text).encode("unicode_escape").decode("ascii")


def _format(error: dict) -> str:
    """One diagnostic as `path: LEVEL kind — first line of message`."""
    path = error.get("path") or "<no path>"
    level = (error.get("level") or "error").upper()
    # `type` is sometimes a bare string and sometimes `[name, [details]]`; the
    # name is the useful half either way.
    kind = error.get("type")
    if isinstance(kind, list) and kind:
        kind = kind[0]
    message = (error.get("message") or "").strip().splitlines()
    head = message[0] if message else "(no message)"
    return f"{_safe(path)}: {level} {_safe(kind)} — {_safe(head)}"


def main(argv: list[str]) -> int:
    passthrough = argv[1:]
    if not passthrough:
        print(f"usage: {Path(argv[0]).name} <semgrep-arg> [<semgrep-arg> ...]", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "semgrep.json"
        cmd = ["semgrep", *passthrough, f"--json-output={report}"]
        # flush: stdout is block-buffered on a pipe (every CI log is one) while
        # the child writes to the same fd directly, so without this the echoed
        # command lands *after* the output it produced. shlex.join: the recipe
        # passes glob patterns like `tools/semgrep/fixtures/*/positive.py`, and an
        # unquoted echo is not what a reader can paste back.
        print(shlex.join(cmd), flush=True)
        try:
            # stdout and stderr inherited, so findings and any semgrep text
            # output appear exactly as they would from a bare recipe line. Only
            # the JSON side-report is consumed here.
            proc = subprocess.run(  # nosec B603  # list argv, no shell; args are the Makefile's
                cmd,
                cwd=REPO_ROOT,
                check=False,
            )
        except OSError as exc:
            print(f"run-semgrep-gate: could not run semgrep: {exc}", file=sys.stderr)
            return 2

        if proc.returncode == 0:
            return 0

        # Non-zero from here on. Say why, or say that semgrep would not say why —
        # never exit non-zero in silence, which is the whole point of this file.
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(f"report is {type(payload).__name__}, not an object")
            errors = payload.get("errors") or []
        except (OSError, ValueError) as exc:
            print(
                f"run-semgrep-gate: semgrep exited {proc.returncode} and its JSON report "
                f"could not be read ({exc}); rerun without --quiet to see its output.",
                file=sys.stderr,
            )
            return proc.returncode

        if not errors:
            # Exit 1 with no errors is the ordinary findings case: `--error` set
            # it and the findings already printed to stdout above.
            if proc.returncode != 1:
                print(
                    f"run-semgrep-gate: semgrep exited {proc.returncode} but reported no "
                    "findings and no errors; rerun without --quiet to see its output.",
                    file=sys.stderr,
                )
            return proc.returncode

        for error in errors:
            print(f"run-semgrep-gate: {_format(error)}", file=sys.stderr)
        print(HINT, file=sys.stderr)
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
