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

import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import posture_harness
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
                # Same posture the ci-security sibling enforces: a job inherits
                # the top-level grant rather than restating it, so `write-all`
                # on the secret-holding job cannot pass.
                check(
                    f"job-permissions[{job_name}]",
                    job.get("permissions") is None,
                )
    # The marker must be a command, not a mention. `eval_steps` is the exemption
    # for the secret-binding check below, so a step that merely names the marker
    # in a shell comment above `npm install -g` could otherwise self-issue it.
    eval_steps = [
        step
        for step in _steps(jobs)
        if any(
            "agentbundle pack evals run" in line and not line.lstrip().startswith("#")
            for line in str(step.get("run", "")).splitlines()
        )
    ]
    check("eval-step-present", bool(eval_steps))
    # Positive, not a two-location denylist. Forbidding only workflow- and
    # job-level `env` left the step-level route open, which is the very sink the
    # comment named: binding the key on the `pip install` or `npm install -g`
    # step reaches the same third-party install scripts. Collect every binding
    # and require the set to be exactly the eval steps.

    def _binds(scope: object) -> bool:
        env = scope.get("env") if isinstance(scope, dict) else None
        return isinstance(env, dict) and "ANTHROPIC_API_KEY" in env

    bound_on: list[str] = []
    if _binds(doc):
        bound_on.append("workflow")
    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            if _binds(job):
                bound_on.append(f"job:{job_name}")
            # A container or service env reaches every step in the job, so it is
            # the same exposure as a job-level binding by another name.
            if _binds(job.get("container")):
                bound_on.append(f"container:{job_name}")
            services = job.get("services")
            if isinstance(services, dict):
                for service_name, service in services.items():
                    if _binds(service):
                        bound_on.append(f"service:{job_name}.{service_name}")
    for index, step in enumerate(_steps(jobs)):
        if _binds(step) and step not in eval_steps:
            bound_on.append(f"step:{step.get('name', index)}")
    check("secret-bound-to-eval-step-only", not bound_on)

    for index, step in enumerate(eval_steps):
        check(
            f"eval-step-report-only[{index}]",
            step.get("continue-on-error") is True,
        )
        # Asserted on the PARSED env value, not as a whole-file substring: a
        # substring is satisfied by a comment that merely names the secret, so
        # swapping the real binding to `vars.` while a comment still spelled
        # `secrets.` passed. PyYAML drops comments, so this needs no
        # comment-stripping helper — and adds no second copy of one.
        env = step.get("env")
        binding = env.get("ANTHROPIC_API_KEY") if isinstance(env, dict) else None
        check(
            f"secret-source[{index}]",
            binding == "${{ secrets.ANTHROPIC_API_KEY }}",
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
        "secret-source[0]",
        lambda text: text.replace(
            "ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}",
            "ANTHROPIC_API_KEY: ${{ vars.ANTHROPIC_API_KEY }}",
            1,
        ),
    ),
    (
        # The hole the whole-file substring left: the real binding moves to
        # `vars.`, and a comment still spelling `secrets.` kept the check green.
        "name-the-secret-in-a-comment-only",
        "secret-source[0]",
        lambda text: text.replace(
            "ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}",
            "ANTHROPIC_API_KEY: ${{ vars.ANTHROPIC_API_KEY }}"
            "  # was secrets.ANTHROPIC_API_KEY",
            1,
        ),
    ),
    (
        "hoist-secret-to-workflow-env",
        "secret-bound-to-eval-step-only",
        lambda text: text.replace(
            "\njobs:\n",
            "\nenv:\n  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n\njobs:\n",
            1,
        ),
    ),
    (
        "hoist-secret-to-job-env",
        "secret-bound-to-eval-step-only",
        lambda text: text.replace(
            "  activation-evals:\n",
            "  activation-evals:\n    env:\n"
            "      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n",
            1,
        ),
    ),
    (
        # The route the two-location denylist left open, and the one its own
        # comment named: the secret in the environment of `npm install -g`.
        "bind-secret-on-the-npm-install-step",
        "secret-bound-to-eval-step-only",
        lambda text: text.replace(
            "      - name: Install the claude CLI (activation detector)\n",
            "      - name: Install the claude CLI (activation detector)\n        env:\n"
            "          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n",
            1,
        ),
    ),
    (
        # A container env reaches every step in the job, including the installs.
        "bind-secret-on-a-job-container",
        "secret-bound-to-eval-step-only",
        lambda text: text.replace(
            "  activation-evals:\n",
            "  activation-evals:\n    container:\n      image: python:3.11\n"
            "      env:\n        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n",
            1,
        ),
    ),
    (
        # The marker in a comment must not self-issue the eval-step exemption.
        "name-the-eval-marker-in-a-comment-only",
        "secret-bound-to-eval-step-only",
        lambda text: text.replace(
            "      - name: Install the claude CLI (activation detector)\n",
            "      - name: Install the claude CLI (activation detector)\n        env:\n"
            "          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n"
            "        # agentbundle pack evals run — see the eval step below\n",
            1,
        ),
    ),
    (
        "grant-job-level-permissions",
        "job-permissions[activation-evals]",
        lambda text: text.replace(
            "  activation-evals:\n",
            "  activation-evals:\n    permissions:\n      contents: write\n",
            1,
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


def self_test() -> int:
    """Prove the real baseline and every evaluated assertion family."""
    return posture_harness.run(
        workflow=WORKFLOW, baseline=_baseline, audit=audit, mutations=_MUTATIONS
    )


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
