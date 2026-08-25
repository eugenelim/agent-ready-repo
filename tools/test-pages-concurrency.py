#!/usr/bin/env python3
"""Mutation-tested concurrency posture check for `.github/workflows/pages.yml`.

A pull-request Pages run must not share a concurrency group with a push/deploy
run, and only pull-request runs may cancel an in-progress run. This deliberately
owns concurrency rather than extending test-pages-workflow.py, whose charter is
the deploy-blocking gate's steps, ordering, and path filters.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pages.yml"
EXPECTED_GROUP = "pages-${{ github.event_name == 'pull_request' && github.ref || github.run_id }}"
EXPECTED_CANCEL = "${{ github.event_name == 'pull_request' }}"
EXPECTED_DEPLOY_IF = "github.ref == 'refs/heads/main'"


def _strip_comments(text: str) -> str:
    """Remove YAML comments so a comment cannot satisfy a posture assertion."""
    lines: list[str] = []
    for line in text.splitlines():
        quote: str | None = None
        cut = len(line)
        for index, char in enumerate(line):
            if quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "#":
                cut = index
                break
        lines.append(line[:cut].rstrip())
    return "\n".join(lines)


def _concurrency_block(text: str) -> str:
    """Return the top-level concurrency mapping, or an empty string."""
    match = re.search(r"^concurrency:\s*$", text, re.M)
    if match is None:
        return ""
    following = text[match.end():]
    next_key = re.search(r"^[A-Za-z][A-Za-z0-9_-]*:\s*$", following, re.M)
    return following[:next_key.start()] if next_key else following


def _job_block(text: str, job_id: str) -> str:
    """Return a job's mapping body, or an empty string when it is absent."""
    match = re.search(rf"^  {re.escape(job_id)}:\s*$", text, re.M)
    if match is None:
        return ""
    following = text[match.end():]
    next_job = re.search(r"^  [A-Za-z0-9_-]+:\s*$", following, re.M)
    return following[:next_job.start()] if next_job else following


def audit(text: str) -> list[str]:
    """Return the concurrency-posture violations in a workflow's text."""
    clean = _strip_comments(text)
    block = _concurrency_block(clean)
    bad: list[str] = []
    if not block:
        return ["concurrency-present"]

    group = re.findall(r"^  group:\s*(.*?)\s*$", block, re.M)
    if group != [EXPECTED_GROUP]:
        bad.append("pr-and-deploy-groups-separated")
    cancel = re.findall(r"^  cancel-in-progress:\s*(.*?)\s*$", block, re.M)
    if cancel != [EXPECTED_CANCEL]:
        bad.append("cancellation-pr-only")
    deploy = _job_block(clean, "deploy")
    deploy_if = re.findall(r"^    if:\s*(.*?)\s*$", deploy, re.M)
    if deploy_if != [EXPECTED_DEPLOY_IF]:
        bad.append("deploy-main-only")
    return bad


def _baseline() -> str:
    if not WORKFLOW.is_file():
        raise SystemExit(f"missing {WORKFLOW} — cannot prove mutations")
    return WORKFLOW.read_text(encoding="utf-8")


_MUTATIONS: tuple[tuple[str, str, str, str], ...] = (
    ("drop-concurrency", "concurrency-present", "concurrency:\n", "concurrency-disabled:\n"),
    ("unkeyed-group", "pr-and-deploy-groups-separated", EXPECTED_GROUP, '"pages"'),
    ("unconditional-cancellation", "cancellation-pr-only", EXPECTED_CANCEL, "true"),
    (
        "widen-deploy-to-pr",
        "deploy-main-only",
        EXPECTED_DEPLOY_IF,
        "github.event_name == 'pull_request' || github.ref == 'refs/heads/main'",
    ),
    ("drop-deploy-if", "deploy-main-only", f"    if: {EXPECTED_DEPLOY_IF}\n", ""),
)


def self_test() -> int:
    """Prove each assertion family catches a concrete unsafe edit."""
    good = _baseline()
    failures: list[str] = []
    if baseline := audit(good):
        failures.append(f"baseline should be clean, got {baseline}")
    for mutation, expected, old, new in _MUTATIONS:
        changed = good.replace(old, new, 1)
        if changed == good:
            failures.append(f"{mutation}: mutation was a no-op")
        elif expected not in audit(changed):
            failures.append(f"{mutation}: expected {expected!r}, got {audit(changed)}")
    if failures:
        print("✖ pages concurrency self-test:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"✓ pages concurrency self-test: {len(_MUTATIONS)} mutations caught")
    return 0


def main() -> int:
    """Run mutation coverage and then validate the repository workflow."""
    if self_test() != 0:
        return 1
    violations = audit(_baseline())
    if violations:
        details = {
            "pr-and-deploy-groups-separated":
                "top-level group must retain the exact documented expression; reread its "
                "deadlock comment before changing it",
            "deploy-main-only":
                "deploy must remain exactly main-only; reread its bare-pages concurrency "
                "comment before changing it",
        }
        print(
            "✖ pages concurrency: " + "; ".join(
                f"{violation} ({details.get(violation, violation)})" for violation in violations
            ),
            file=sys.stderr,
        )
        return 1
    print("✓ pages.yml concurrency posture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
