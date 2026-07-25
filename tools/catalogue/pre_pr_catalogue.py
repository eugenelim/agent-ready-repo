#!/usr/bin/env python3
"""Catalogue pre-PR check — portable verify + repo-specific gates.

Portable verification (lint, build, schema, self-host drift) is delegated to:
  agentbundle catalogue verify --root .

This script then runs the repo-specific policy gates that are never projected
to adopters (spec state, traceability, brief coverage, and the eight
catalogue-internal linters).

`make pre-pr` and `make build-check` run this (via the shim at
tools/pre-pr-catalogue.py); the `docs.yml` CI aggregator (`hooks` job) targets
it directly. Exits non-zero on the first failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# tools/catalogue/ → tools/ → repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_AGENTBUNDLE_PATH = str(_REPO_ROOT / "packages" / "agentbundle")


def _agentbundle_env() -> dict:
    """Env with packages/agentbundle on PYTHONPATH for subprocess agentbundle calls."""
    env = os.environ.copy()
    pp = env.get("PYTHONPATH", "")
    parts = [p for p in pp.split(os.pathsep) if p]
    if _AGENTBUNDLE_PATH not in parts:
        env["PYTHONPATH"] = os.pathsep.join([_AGENTBUNDLE_PATH] + parts)
    return env


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

    # Step 1: portable verification — lint, build output, schema, self-host drift.
    # Delegates to the canonical engine; never duplicate portable logic here.
    rc = subprocess.run(
        [py, "-m", "agentbundle", "catalogue", "verify", "--root", "."],
        check=False,
        env=_agentbundle_env(),
    )
    if rc.returncode != 0:
        print("pre-pr: ✖ catalogue verify failed", file=sys.stderr)
        sys.exit(rc.returncode)
    print("pre-pr: ✓ catalogue verify")

    # Step 2: repo-specific gates (catalogue-internal checks + adopter-facing hook).
    _run("agents-md hygiene",   [py, "tools/lint-agents-md.py"])
    _run("agent-artifact lint", [py, "tools/lint-agent-artifacts.py"])
    _run("skill-spec lint",     [py, "tools/lint-skill-spec.py"])
    _run("knowledge lint",      [py, "tools/lint-knowledge.py"])
    _run("build lint",          [py, "tools/lint-build.py"])
    _run("catalogue-seeds lint", [py, "tools/lint-catalogue-seeds.py"])
    _run("catalogue-seeds lint self-test",
         [py, "tools/test-lint-catalogue-seeds.py"])
    _run("credentialed-skill lint", [py, "tools/lint_credentialed_skills.py"])
    _run("credentialed-skill lint self-test",
         [py, "tools/test-lint-credentialed-skills.py"])
    _run("sso-config lint", [py, "tools/lint-sso-config.py"])
    _run("sso-config lint self-test", [py, "tools/test-lint-sso-config.py"])
    _run("knowledge-surface parity", [py, "tools/lint-knowledge-surface-parity.py"])
    _run("knowledge-surface parity self-test",
         [py, "tools/test-lint-knowledge-surface-parity.py"])
    _run("profiles lint", [py, "tools/lint-profiles.py", "--root", "."])
    _run("profiles lint self-test", [py, "tools/test-lint-profiles.py"])
    _run("pack-evals runner self-test", [py, "tools/test-run-pack-evals.py"])
    _run("pack-evals workflow posture", [py, "tools/test-pack-evals-workflow.py"])
    _run("web-journey parity", [py, "tools/lint-web-journey-parity.py"])
    _run("web-journey parity self-test",
         [py, "tools/test-lint-web-journey-parity.py"])

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
