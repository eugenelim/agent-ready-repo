#!/usr/bin/env python3
"""Fail `make sast` when the local semgrep is outside the manifest's pinned range.

Presence is not enough for semgrep, unlike the tools around it. Its per-rule
timeouts and its `--strict` diagnostics are engine behaviour that moves between
releases, and `SEMGREP_EXCLUDE`'s justification is a set of measurements taken at
a specific version. A local semgrep outside the pinned range produces evidence
that does not describe what CI installs — which is how that block's figures were
once taken eight releases early.

Both bounds matter. Below the floor is the case that already happened; above the
ceiling is the same defect mirrored, because `tools/requirements-sast.txt` caps
the range and CI would never install past it.

The range is read from the manifest rather than restated here, so the two cannot
drift. Unlike `tools/run-semgrep-gate.py`, this needs no stub-driven self-test:
it has no silent-success path — every branch either exits 0 having compared two
parsed versions, or exits non-zero after printing which check failed.

Run: python3 tools/check-semgrep-version.py
Exit 0 = in range; 1 = out of range or undeterminable.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "semgrep"
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "tools" / "requirements-sast.txt"
# `semgrep>=1.174,<2` — the ceiling is optional so a future unbounded pin still works.
SPEC = re.compile(r"^semgrep\s*>=\s*([0-9][0-9.]*)\s*(?:,\s*<\s*([0-9][0-9.]*))?", re.M)
# semgrep prints the bare version to stdout; the upgrade notice goes to stderr.
# Matched rather than assumed, so a stray banner or a `v` prefix cannot be parsed
# as a version component.
VERSION = re.compile(r"\b([0-9]+(?:\.[0-9]+)+)\b")


def _parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def fail(message: str) -> int:
    print(f"make sast: {message}", file=sys.stderr)
    return 1


def main() -> int:
    try:
        spec = SPEC.search(MANIFEST.read_text(encoding="utf-8"))
    except OSError as exc:
        return fail(f"could not read {MANIFEST.name}: {exc}")
    if not spec:
        return fail(f"no `semgrep>=` pin found in {MANIFEST.name}; cannot check the version")
    floor, ceiling = spec.group(1), spec.group(2)

    try:
        proc = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is a literal
            ["semgrep", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return fail(f"could not run `semgrep --version`: {exc}")

    found = VERSION.search(proc.stdout)
    if not found:
        # Distinct from the out-of-range message on purpose: telling someone their
        # correct semgrep is "below the floor" is how a security gate gets bypassed.
        return fail(
            "could not parse a version from `semgrep --version` "
            f"(stdout: {proc.stdout.strip()!r}); cannot confirm it matches "
            f"{MANIFEST.name}'s pin"
        )
    have = found.group(1)

    if _parts(have) < _parts(floor):
        return fail(
            f"semgrep {have} is below the {floor} floor in {MANIFEST.name} — "
            "run: pip install -r tools/requirements-sast.txt"
        )
    if ceiling and _parts(have) >= _parts(ceiling):
        return fail(
            f"semgrep {have} is at or above the {ceiling} ceiling in {MANIFEST.name}, "
            "so it is not what CI installs — run: pip install -r tools/requirements-sast.txt"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
