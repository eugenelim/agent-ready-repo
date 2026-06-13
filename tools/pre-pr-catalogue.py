#!/usr/bin/env python3
"""Catalogue-only pre-PR gate (repo-native — NEVER projected to adopters).

This is *this catalogue's* full pre-PR gate: the 8 catalogue-internal checks
(which enforce the catalogue's own conventions on its own `.apm/`, seeds, and
build pipeline) followed by the adopter-facing `tools/hooks/pre-pr.py` (the
work-loop caps gate). Adopters get only the shipped `pre-pr.py`; they never see
this file — the catalogue linters are meaningless in an adopter's tree (see
`AGENTS.local.md` § adopter-facing vs local-only).

`make pre-pr` and `make build-check` run this; the `docs.yml` CI aggregator
(`hooks` job) and `tools/test-pre-pr.sh` target it too.

Exits non-zero on the first failure.
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


def _run(label: str, argv: list[str]) -> None:
    """Run *argv*; on non-zero exit, surface its output, print the failure line,
    and ``sys.exit(1)``. On success, print the success line.

    NOTE: unlike the shipped ``tools/hooks/pre-pr.py`` twin, this catalogue
    ``_run`` does **not** skip on a missing tool — a deleted catalogue linter
    must fail loud, not silently pass. Do not "unify" the two `_run`s: that
    would make a dropped catalogue check go green (a real regression)."""
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        print(f"pre-pr: ✖ {label} failed", file=sys.stderr)
        sys.exit(1)
    print(f"pre-pr: ✓ {label}")


def main() -> int:
    repo_root = _repo_root()
    os.chdir(repo_root)

    py = sys.executable  # parent interpreter for child scripts

    # The catalogue-internal checks, in the order the old pre-pr.py ran them
    # (later additions — self-tests, the knowledge-surface parity gate — append).
    _run("agents-md hygiene",   [py, "tools/lint-agents-md.py"])
    _run("agent-artifact lint", [py, "tools/lint-agent-artifacts.py"])
    _run("skill-spec lint",     [py, "tools/lint-skill-spec.py"])
    _run("knowledge lint",      [py, "tools/lint-knowledge.py"])
    _run("build lint",          [py, "tools/lint-build.py"])
    _run("seeds lint",          [py, "tools/lint-seeds.py"])
    _run("credentialed-skill lint", [py, "tools/lint_credentialed_skills.py"])
    _run("credentialed-skill lint self-test",
         [py, "tools/test-lint-credentialed-skills.py"])
    _run("knowledge-surface parity", [py, "tools/lint-knowledge-surface-parity.py"])
    _run("knowledge-surface parity self-test",
         [py, "tools/test-lint-knowledge-surface-parity.py"])

    # Delegate to the shipped adopter-facing hook for the work-loop caps gate.
    result = subprocess.run(
        [py, "tools/hooks/pre-pr.py"], check=False,
    )
    if result.returncode != 0:
        # The shipped hook already printed its own ✖ line.
        sys.exit(result.returncode)

    return 0


if __name__ == "__main__":
    sys.exit(main())
