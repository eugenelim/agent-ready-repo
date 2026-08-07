#!/usr/bin/env python3
"""Self-test for tools/semgrep/argv-path-boundary.yml.

The rule is excluded from `make sast`'s scan of its own fixtures (see
SEMGREP_EXCLUDE in the Makefile), so without this file the fixtures would be
dead weight and the rule would be unproven. This is the gate that keeps them
honest.

Asserts three things:
  1. The rule FIRES on the pre-fix shape (positive fixture) — a rule that
     never fires is indistinguishable from no rule at all.
  2. The rule is SILENT on both post-fix shapes (negative fixture): the
     `_validated_root(...)` validator, and the pre-existing
     resolve()-then-is_relative_to() exemplar from check-spec-status.py.
  3. The rule is SILENT on the three production scripts it is scoped to,
     i.e. the fix actually satisfies it.

Run: python3 tools/test-semgrep-argv-boundary.py
Exit 0 = all pass; exit non-zero = at least one failure. Skips (exit 0) when
semgrep is not installed, matching `make sast`'s optional-tool posture.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
RULE = REPO_ROOT / "tools" / "semgrep" / "argv-path-boundary.yml"
FIXTURES = REPO_ROOT / "tools" / "semgrep" / "fixtures" / "argv-path-boundary"

SCRIPTS_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
FIXED_SCRIPTS = [
    SCRIPTS_DIR / "lint-traceability.py",
    SCRIPTS_DIR / "lint-spec-status.py",
    SCRIPTS_DIR / "loop-cohort.py",
]

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


def scan(target: Path) -> list[dict]:
    """Run the rule over `target`; return its findings."""
    proc = subprocess.run(
        [
            "semgrep", "--config", str(RULE),
            "--json", "--quiet", "--metrics", "off", str(target),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(REPO_ROOT),
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"semgrep produced no output for {target} — stderr: {proc.stderr}")
    return json.loads(proc.stdout)["results"]


def test_positive_fixture_fires() -> None:
    name = "positive fixture fires exactly once"
    hits = scan(FIXTURES / "positive.py")
    if len(hits) != 1:
        fail(name, f"expected 1 finding, got {len(hits)}: {[h['start']['line'] for h in hits]}")
    else:
        ok(name)


def test_negative_fixture_silent() -> None:
    name = "negative fixture is silent (validator + is_relative_to exemplar)"
    hits = scan(FIXTURES / "negative.py")
    if hits:
        lines = [h["start"]["line"] for h in hits]
        fail(name, f"expected 0 findings, got {len(hits)} at lines {lines}")
    else:
        ok(name)


def test_fixed_scripts_silent() -> None:
    for script in FIXED_SCRIPTS:
        name = f"{script.name} is silent after the fix"
        if not script.is_file():
            fail(name, f"subject not found at {script} — path drifted?")
            continue
        hits = scan(script)
        if hits:
            lines = [h["start"]["line"] for h in hits]
            fail(name, f"expected 0 findings, got {len(hits)} at lines {lines}")
        else:
            ok(name)


def main() -> int:
    if shutil.which("semgrep") is None:
        print("skip: semgrep not on PATH (install: pip install -r tools/requirements-sast.txt)")
        return 0
    if not RULE.is_file():
        print(f"FAIL: rule not found at {RULE}", file=sys.stderr)
        return 1

    test_positive_fixture_fires()
    test_negative_fixture_silent()
    test_fixed_scripts_silent()

    total = ran
    passed = total - len(failures)
    print(f"\n{passed}/{total} passed")
    if failures:
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
