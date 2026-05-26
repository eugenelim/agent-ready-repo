#!/usr/bin/env python3
"""Pre-PR hook: runs every artifact linter and the work-loop's
mechanical termination check against any active spec state. Exits
non-zero on the first failure so a contributor can't open a PR
whose artifacts are inconsistent with the conventions.

Pure-stdlib Python port of pre-pr.sh. Native-Windows-parity companion
of the bash version: same four linters in the same order, same
state.json iteration shape, same `pre-pr: ✓ <label>` /
`pre-pr: ✖ <label> failed` / `pre-pr: all checks passed` output.

What it runs:
  - tools/lint-agents-md.py        — root AGENTS.md hygiene, drift-watch
  - tools/lint-agent-artifacts.py  — skill/agent/command frontmatter
  - tools/lint-skill-spec.py       — agentskills.io spec compliance
  - tools/lint-knowledge.py        — docs/knowledge/patterns.jsonl
  - tools/lint-build.py            — build-pipeline hygiene
  - tools/lint-seeds.py            — pack seeds placeholder shape (RFC-0002)
  - tools/lint-credentialed-skills.sh
                                   — broker-agnostic + per-broker checks
                                      (RFC-0013, spec credential-broker-contract)
  - .claude/skills/work-loop/scripts/loop-cohort.py
                                   — for each docs/specs/*/state.json,
                                      `loop-cohort.py check <spec-dir>` in
                                      --phase implement and --phase review

Wiring lives in each tool's hook surface (Claude Code:
.claude/settings.json; see tools/hooks/README.md).
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
    """Run *argv*; on non-zero exit, print the bash-parity failure
    line and `sys.exit(1)`. On success, print the parity success line."""
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        # Surface the linter's own output before the aggregator's failure
        # line so the contributor sees both. Bash version redirects > /dev/null
        # so the linter output is suppressed — we keep parity on the exit/label
        # behaviour and surface the linter output for debuggability since the
        # bash > /dev/null silenced useful diagnostics.
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

    py = sys.executable  # use parent's interpreter for child linters

    _run("agents-md hygiene",   [py, "tools/lint-agents-md.py"])
    _run("agent-artifact lint", [py, "tools/lint-agent-artifacts.py"])
    _run("skill-spec lint",     [py, "tools/lint-skill-spec.py"])
    _run("knowledge lint",      [py, "tools/lint-knowledge.py"])
    _run("build lint",          [py, "tools/lint-build.py"])
    _run("seeds lint",          [py, "tools/lint-seeds.py"])
    _run("credentialed-skill lint", [py, "tools/lint_credentialed_skills.py"])
    _run("credentialed-skill lint self-test",
         [py, "tools/test-lint-credentialed-skills.py"])

    state_files = sorted(Path("docs/specs").glob("*/state.json"))
    if not state_files:
        print("pre-pr: (no active state.json — skipping loop-cohort check)")
    else:
        loop_cohort = Path(".claude/skills/work-loop/scripts/loop-cohort.py")
        for state in state_files:
            spec_dir = state.parent
            for phase in ("implement", "review"):
                result = subprocess.run(
                    [py, str(loop_cohort), "check", str(spec_dir), "--phase", phase],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    if result.stdout:
                        sys.stdout.write(result.stdout)
                    if result.stderr:
                        sys.stderr.write(result.stderr)
                    print(
                        f"pre-pr: ✖ loop-cohort check {spec_dir} --phase {phase} failed",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                print(f"pre-pr: ✓ loop-cohort check {spec_dir} ({phase})")

    print("pre-pr: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
