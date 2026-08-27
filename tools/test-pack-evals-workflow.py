#!/usr/bin/env python3
"""Posture test for ``.github/workflows/pack-evals.yml``.

This workflow is the repository's managed-secret boundary for activation evals.
It must remain schedule/manual-only so an untrusted fork pull request cannot
reach ``ANTHROPIC_API_KEY``.  The mutation matrix runs on every invocation: a
posture assertion without a mutation that makes it fail is not treated as proof.

The baseline is the real workflow, deliberately.  If the workflow itself is
weakened, the harness fails before it can claim that any derived mutation was
caught.  Pure-stdlib plus PyYAML (already a tools dependency).
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

# Windows cp1252 guard — reconfigure stdout/stderr before printing verdict marks.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pack-evals.yml"
# The workflow header claims "schedule + workflow_dispatch ONLY", so the check
# has to be an allowlist. A denylist of the three obvious fork triggers admits
# `workflow_run` and `issue_comment`, which do run in base context with secrets.
ALLOWED_TRIGGERS = frozenset({"schedule", "workflow_dispatch"})

Mutation = tuple[str, str, Callable[[str], str]]


def _steps(jobs: object) -> Iterable[dict[Any, Any]]:
    """Yield mapping-shaped steps from jobs whose step collection is a list."""
    if not isinstance(jobs, dict):
        return
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if isinstance(step, dict):
                yield step


def audit(text: str, evaluated: list[str] | None = None) -> list[str]:
    """Return stable violation labels for one workflow text.

    ``text == ""`` is the pure-function representation of a missing workflow;
    the CLI maps a missing file to that value rather than exiting through an
    untestable imperative branch.
    """
    violations: list[str] = []

    def check(label: str, condition: bool) -> None:
        if evaluated is not None:
            evaluated.append(label)
        if not condition:
            violations.append(label)

    check("workflow-file-present", bool(text))
    if not text:
        return violations

    try:
        loaded: Any = yaml.safe_load(text)
    except yaml.YAMLError:
        check("yaml-parses", False)
        return violations
    check("yaml-parses", isinstance(loaded, dict))
    if not isinstance(loaded, dict):
        return violations
    doc: dict[Any, Any] = loaded

    # PyYAML 1.1 resolves the bareword ``on`` as boolean True.
    triggers = doc.get("on", doc.get(True))
    check("triggers-mapping", isinstance(triggers, dict))
    if isinstance(triggers, dict):
        check(
            "triggers-required",
            "schedule" in triggers and "workflow_dispatch" in triggers,
        )
        for forbidden in ("push", "pull_request", "pull_request_target"):
            check(f"trigger-forbidden[{forbidden}]", forbidden not in triggers)
        # The named three stay above so a regression to any of them reports the
        # specific trigger. This closes the gap between them and the "only"
        # claimed by the docstring and the printed verdict.
        check(
            "triggers-allowlist",
            {str(name) for name in triggers} <= set(ALLOWED_TRIGGERS),
        )

    check("permissions-read", doc.get("permissions") == {"contents": "read"})

    # The key must cross the Actions secrets boundary rather than coming from a
    # variable or a hard-coded value.
    check("secret-source", "secrets.ANTHROPIC_API_KEY" in text)

    jobs = doc.get("jobs")
    check(
        "jobs-mapping",
        isinstance(jobs, dict)
        and bool(jobs)
        and all(isinstance(job, dict) for job in jobs.values()),
    )
    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if isinstance(job, dict):
                check(
                    f"job-steps-list[{job_name}]",
                    isinstance(job.get("steps", []), list),
                )
    eval_steps = [
        step
        for step in _steps(jobs)
        if "agentbundle pack evals run" in str(step.get("run", ""))
    ]
    check("eval-step-present", bool(eval_steps))
    for index, step in enumerate(eval_steps):
        check(
            f"eval-step-report-only[{index}]",
            step.get("continue-on-error") is True,
        )

    upload_steps = [
        step
        for step in _steps(jobs)
        if "upload-artifact" in str(step.get("uses", ""))
    ]
    check("upload-step-present", bool(upload_steps))
    for index, step in enumerate(upload_steps):
        with_block = step.get("with")
        path = str(with_block.get("path", "")) if isinstance(with_block, dict) else ""
        check(f"upload-summary-only[{index}]", "summary.json" in path)
        check(f"upload-excludes-outputs[{index}]", "outputs" not in path)

    return violations


def _baseline() -> str:
    """Return the real workflow, or the empty missing-file sentinel."""
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    return ""


_MUTATIONS: list[Mutation] = [
    (
        "remove-workflow-file",
        "workflow-file-present",
        lambda _text: "",
    ),
    (
        "break-yaml",
        "yaml-parses",
        lambda _text: "[unterminated\n",
    ),
    (
        "replace-trigger-map-with-list",
        "triggers-mapping",
        lambda text: text.replace("on:\n", "on: []\nlegacy-on:\n", 1),
    ),
    (
        "drop-schedule-trigger",
        "triggers-required",
        lambda text: text.replace("  schedule:\n", "  cadence:\n", 1),
    ),
    (
        "add-fork-pr-trigger",
        "trigger-forbidden[pull_request]",
        lambda text: text.replace("on:\n", "on:\n  pull_request:\n", 1),
    ),
    (
        # Not on the denylist, and it runs in base context with secrets — the
        # case that made presence-of-three insufficient.
        "add-workflow-run-trigger",
        "triggers-allowlist",
        lambda text: text.replace(
            "on:\n",
            "on:\n  workflow_run:\n    workflows: [build-check]\n"
            "    types: [completed]\n",
            1,
        ),
    ),
    (
        "widen-token-permissions",
        "permissions-read",
        lambda text: text.replace("  contents: read\n", "  contents: write\n", 1),
    ),
    (
        "move-api-key-out-of-secrets",
        "secret-source",
        lambda text: text.replace(
            "secrets.ANTHROPIC_API_KEY", "vars.ANTHROPIC_API_KEY", 1
        ),
    ),
    (
        "add-malformed-job",
        "jobs-mapping",
        lambda text: text.replace("jobs:\n", "jobs:\n  malformed: true\n", 1),
    ),
    (
        "add-job-with-malformed-steps",
        "job-steps-list[malformed]",
        lambda text: text.replace(
            "jobs:\n", "jobs:\n  malformed:\n    steps: true\n", 1
        ),
    ),
    (
        "remove-eval-invocation",
        "eval-step-present",
        lambda text: text.replace(
            "agentbundle pack evals run", "agentbundle pack evaluations run", 1
        ),
    ),
    (
        "make-eval-blocking",
        "eval-step-report-only[0]",
        lambda text: text.replace(
            "        continue-on-error: true\n",
            "        continue-on-error: false\n",
            1,
        ),
    ),
    (
        "remove-artifact-upload",
        "upload-step-present",
        lambda text: text.replace("actions/upload-artifact@", "actions/download-artifact@", 1),
    ),
    (
        "replace-summary-artifact",
        "upload-summary-only[0]",
        lambda text: text.replace(
            ".eval-workspace/**/summary.json",
            ".eval-workspace/**/report.json",
            1,
        ),
    ),
    (
        "include-model-outputs",
        "upload-excludes-outputs[0]",
        lambda text: text.replace(
            ".eval-workspace/**/summary.json",
            ".eval-workspace/**/outputs/**/summary.json",
            1,
        ),
    ),
]


def _family(label: str) -> str:
    """Collapse repeated indexed assertions into one mutation family."""
    return re.sub(r"\[.*\]$", "[*]", label)


def self_test() -> int:
    """Prove the real baseline and every evaluated assertion family."""
    failures: list[str] = []
    good = _baseline()
    evaluated: list[str] = []
    baseline_violations = audit(good, evaluated)
    if baseline_violations:
        # Return before the matrix. Every transform is pinned to the real
        # workflow's text, so a dirty or missing baseline turns each one into a
        # no-op — or, where a transform asserts its literal, into an exception —
        # burying the one true cause under a wall of derived noise that names
        # neither the cause nor the file to edit.
        print(
            f"\u2716 self-test: {WORKFLOW} is not clean; "
            f"{len(baseline_violations)} posture violation(s) before any mutation:",
            file=sys.stderr,
        )
        for violation in baseline_violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    for mutation_id, expected, transform in _MUTATIONS:
        mutated = transform(good)
        if mutated == good:
            failures.append(
                f"{mutation_id}: transform was a no-op against {WORKFLOW.name} — "
                "proves nothing; re-pin its literal against that file"
            )
            continue
        got = audit(mutated)
        if expected not in got:
            failures.append(f"{mutation_id}: expected {expected!r}, got {got}")

    covered = {_family(expected) for _, expected, _ in _MUTATIONS}
    uncovered = sorted({_family(label) for label in evaluated} - covered)
    if uncovered:
        failures.append(f"assertion families evaluated but unmutated: {uncovered}")

    if failures:
        print(f"✖ self-test: {len(failures)} problem(s):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(
        f"✓ self-test: baseline clean; {len(_MUTATIONS)} mutations each caught; "
        f"every one of {len(covered)} assertion families has ≥1 mutation"
    )
    return 0


def main(argv: list[str]) -> int:
    """Run the harness, then audit the repository workflow."""
    if "--self-test" in argv:
        return self_test()
    if self_test() != 0:
        return 1

    violations = audit(_baseline())
    if violations:
        print(f"✖ pack-evals.yml: {len(violations)} posture violation(s):", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print(
        "✓ pack-evals.yml posture OK: schedule+dispatch only, contents:read, "
        "secret-backed key, report-only evals, bounded summaries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
