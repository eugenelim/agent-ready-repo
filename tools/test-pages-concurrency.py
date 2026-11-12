#!/usr/bin/env python3
"""Mutation-tested concurrency posture check for `.github/workflows/pages.yml`.

A pull-request Pages run must not share a concurrency group with a push/deploy
run, and only pull-request runs may cancel an in-progress run. This deliberately
owns concurrency rather than extending test-pages-workflow.py, whose charter is
the deploy-blocking gate's steps, ordering, and path filters.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pages.yml"
EXPECTED_GROUP = "pages-${{ github.event_name == 'pull_request' && github.ref || github.run_id }}"
EXPECTED_CANCEL = "${{ github.event_name == 'pull_request' }}"
EXPECTED_DEPLOY_IF = "github.ref == 'refs/heads/main'"
PUBLISH_IF = "steps.current-main.outputs.publish == 'true'"
GUARD_SCRIPT = '''latest=$(gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" --jq '.object.sha')
[[ "$latest" =~ ^[0-9a-f]{40}$ ]] || exit 1
if [ "$GITHUB_SHA" = "$latest" ]; then
  echo "publish=true" >> "$GITHUB_OUTPUT"
else
  echo "publish=false" >> "$GITHUB_OUTPUT"
fi'''


def _guard_script(text: str) -> str:
    """Read the literal guard body from the serialized deploy job."""
    match = re.search(r"^        run: \|\n((?:          .*\n?)+)", text, re.M)
    return "\n".join(line[10:] for line in match[1].splitlines()) if match else ""


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
    if re.findall(r"^    needs:\s*(.*?)\s*$", deploy, re.M) != ["build"]:
        bad.append("deploy-needs-build")
    if not re.search(r"^    concurrency:\n      group: pages\n      cancel-in-progress: false$", deploy, re.M):
        bad.append("deploy-serialized")
    if not re.search(r"^    permissions:\n      contents: read$", deploy, re.M):
        bad.append("guard-can-read-main")
    if _guard_script(deploy) != GUARD_SCRIPT:
        bad.append("latest-main-guard")
    if not re.search(
        r"^      - name: Check current main before publishing\n"
        r"        id: current-main\n        env:\n"
        r"          GH_TOKEN: \$\{\{ github.token \}\}\n"
        r"        shell: bash\n        run: \|", deploy, re.M
    ):
        bad.append("guard-wiring")
    if not re.search(
        r"^      - name: Deploy to GitHub Pages\n"
        rf"        if: {re.escape(PUBLISH_IF)}\n", deploy, re.M
    ):
        bad.append("publish-current-main-only")
    if deploy.find("id: current-main") > deploy.find("- name: Deploy to GitHub Pages"):
        bad.append("guard-before-publish")
    if re.search(r"^\s+continue-on-error:\s*(?!false\s*$)\S+", deploy, re.M):
        bad.append("deploy-fails-closed")
    guard = re.search(r"^      - name: Check current main before publishing\n(.*?)(?=^      - |\Z)", deploy, re.M | re.S)
    if guard and re.search(r"^        if:", guard[1], re.M):
        bad.append("guard-unconditional")
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
    ("drop-read-permission", "guard-can-read-main", "      contents: read\n", ""),
    ("drop-build-dependency", "deploy-needs-build", "    needs: build\n", ""),
    ("cancel-production", "deploy-serialized", "      cancel-in-progress: false", "      cancel-in-progress: true"),
    ("change-production-group", "deploy-serialized", "      group: pages\n", "      group: other\n"),
    ("drop-guard", "latest-main-guard", GUARD_SCRIPT.splitlines()[0], "true"),
    ("invert-comparison", "latest-main-guard", '"$GITHUB_SHA" = "$latest"', '"$GITHUB_SHA" != "$latest"'),
    ("allow-stale", "latest-main-guard", 'echo "publish=false"', 'echo "publish=true"'),
    ("drop-token", "guard-wiring", "          GH_TOKEN: ${{ github.token }}\n", ""),
    ("rename-guard", "guard-wiring", "id: current-main", "id: other"),
    ("drop-publish-condition", "publish-current-main-only", f"        if: {PUBLISH_IF}\n", ""),
    ("ignore-guard-failure", "deploy-fails-closed", "        id: current-main\n", "        id: current-main\n        continue-on-error: true\n"),
    ("skip-guard", "guard-unconditional", "        id: current-main\n", "        id: current-main\n        if: false\n"),
)


def _behavior_failures(text: str) -> list[str]:
    """Execute the workflow's shell against a local API stub, without network."""
    failures: list[str] = []
    script = _guard_script(_job_block(text, "deploy"))
    with tempfile.TemporaryDirectory(prefix="pages-guard-") as directory:
        root = Path(directory)
        gh = root / "gh"
        gh.write_text('#!/bin/sh\nprintf "%s\\n" "$TIP"\nexit "$API_EXIT"\n', encoding="utf-8")
        gh.chmod(0o700)
        for label, tip, api_exit, expected in (
            ("current", "a" * 40, "0", "publish=true\n"),
            ("stale", "b" * 40, "0", "publish=false\n"),
            ("lookup-failure", "a" * 40, "1", ""),
            ("empty-tip", "", "0", ""),
            ("malformed-tip", "null", "0", ""),
        ):
            output = root / label
            env = dict(os.environ, PATH=f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
                       GITHUB_SHA="a" * 40, GITHUB_REPOSITORY="example/project",
                       GITHUB_OUTPUT=str(output), TIP=tip, API_EXIT=api_exit)
            result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script],
                                    env=env, capture_output=True, text=True, check=False)
            actual = output.read_text(encoding="utf-8") if output.exists() else ""
            if actual != expected or (result.returncode == 0) != bool(expected):
                failures.append(f"{label}: exit={result.returncode}, output={actual!r}")
    return failures


def self_test() -> int:
    """Prove each assertion family catches a concrete unsafe edit."""
    good = _baseline()
    failures: list[str] = []
    failures.extend(_behavior_failures(good))
    if baseline := audit(good):
        failures.append(f"baseline should be clean, got {baseline}")
    for mutation, expected, old, new in _MUTATIONS:
        changed = good.replace(old, new, 1)
        if changed == good:
            failures.append(f"{mutation}: mutation was a no-op")
        elif expected not in audit(changed):
            failures.append(f"{mutation}: expected {expected!r}, got {audit(changed)}")
    guard_start = good.index("      - name: Check current main before publishing")
    publish_start = good.index("      - name: Deploy to GitHub Pages")
    reordered = good[:guard_start] + good[publish_start:] + good[guard_start:publish_start]
    if "guard-before-publish" not in audit(reordered):
        failures.append("guard moved after publication was not rejected")
    if failures:
        print("✖ pages concurrency self-test:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"✓ pages concurrency self-test: {len(_MUTATIONS) + 1} mutations caught; 5 shell cases passed")
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
