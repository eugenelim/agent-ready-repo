#!/usr/bin/env python3
"""Fail CI only for zizmor's excessive-permissions audit in owned workflows.

The broad zizmor gate intentionally retains its high-severity floor. Lowering it
would also make the repository's unrelated medium/low findings block this job.
This focused companion run keeps `excessive-permissions` continuously enforced
for the two workflows closed by the CI-posture backlog item.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = (
    ".github/workflows/build-check-windows.yml",
    ".github/workflows/codeql.yml",
)
AUDIT = "excessive-permissions"
CODEQL = ".github/workflows/codeql.yml"
CODEQL_TOP_LEVEL_FLOOR = "permissions:\n  contents: read\n"
CODEQL_ANALYZE_PERMISSIONS = (
    "    permissions:\n"
    "      security-events: write\n"
    "      contents: read\n"
    "      actions: read\n"
)


def _job_block(workflow: str, job_id: str) -> str:
    """Return one two-space-indented job block, excluding YAML comments."""
    clean = "\n".join(line.split("#", 1)[0].rstrip() for line in workflow.splitlines())
    match = re.search(rf"^  {re.escape(job_id)}:\s*$", clean, re.M)
    if match is None:
        return ""
    following = clean[match.end():]
    next_job = re.search(r"^  [A-Za-z0-9_-]+:\s*$", following, re.M)
    return following[:next_job.start()] if next_job else following


def _check_codeql_permission_shape() -> str | None:
    """Validate CodeQL's future-job floor and analyzer-only elevation."""
    path = REPO_ROOT / CODEQL
    workflow = path.read_text(encoding="utf-8")
    if workflow.count(CODEQL_TOP_LEVEL_FLOOR) != 1:
        return "codeql.yml must retain top-level permissions: contents: read"
    analyze = _job_block(workflow, "analyze")
    if analyze.count(CODEQL_ANALYZE_PERMISSIONS) != 1:
        return "codeql.yml analyze job must retain its scoped CodeQL permissions"
    return None


def main() -> int:
    """Run zizmor and fail when its focused audit reports a finding."""
    missing = [path for path in WORKFLOWS if not (REPO_ROOT / path).is_file()]
    if missing:
        print(
            f"zizmor excessive-permissions: owned workflow missing: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2
    if problem := _check_codeql_permission_shape():
        print(f"zizmor excessive-permissions: {problem}", file=sys.stderr)
        return 1

    command = [
        "zizmor", "--no-exit-codes", "--min-severity", "low", "--format", "json", *WORKFLOWS,
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("zizmor excessive-permissions: invalid JSON output", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return 2
    if not isinstance(findings, list):
        print("zizmor excessive-permissions: JSON result is not a list", file=sys.stderr)
        return 2

    violations = [finding for finding in findings if finding.get("ident") == AUDIT]
    if violations:
        print(
            f"zizmor excessive-permissions: {len(violations)} finding(s) in "
            f"{', '.join(WORKFLOWS)}",
            file=sys.stderr,
        )
        for finding in violations:
            for location in finding.get("locations", []):
                path = location.get("symbolic", {}).get("key", {}).get("Local", {})
                print(f"  - {path.get('verbatim_path', 'unknown workflow')}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(f"zizmor excessive-permissions: zizmor exited {result.returncode}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    print("zizmor excessive-permissions: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
