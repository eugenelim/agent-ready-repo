#!/usr/bin/env python3
"""Posture check for .github/workflows/pack-evals.yml (pack-activation-evals
AC8 / AC9 / AC10). Security-load-bearing: the schedule-only trigger keeps an
untrusted-fork PR from reaching the ANTHROPIC_API_KEY secret, and the
least-privilege permissions block keeps a compromised run from pushing commits.

Pure-stdlib + PyYAML (already a tools/ dependency). Asserts a posture rather
than running the workflow.
"""

from __future__ import annotations

import pathlib
import sys

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pack-evals.yml"


def fail(msg: str) -> None:
    print(f"✖ pack-evals.yml: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not WORKFLOW.exists():
        fail(f"not found at {WORKFLOW}")
    text = WORKFLOW.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"does not parse as YAML: {exc}")

    # PyYAML parses the bareword `on:` key as the boolean True.
    triggers = doc.get("on", doc.get(True))
    if not isinstance(triggers, dict):
        fail("`on:` must be a mapping of trigger types")
    if "schedule" not in triggers or "workflow_dispatch" not in triggers:
        fail("must trigger on both `schedule` and `workflow_dispatch`")
    for forbidden in ("push", "pull_request", "pull_request_target"):
        if forbidden in triggers:
            fail(
                f"must NOT trigger on `{forbidden}` — an untrusted-fork PR could "
                f"reach the ANTHROPIC_API_KEY secret (AC8)"
            )

    # Least-privilege permissions (AC9).
    perms = doc.get("permissions")
    if perms != {"contents": "read"}:
        fail(f"top-level permissions must be {{contents: read}}, got {perms!r}")

    # Consumes the API key from secrets (AC8), never a hardcoded value.
    if "secrets.ANTHROPIC_API_KEY" not in text:
        fail("must consume ANTHROPIC_API_KEY from repo secrets")

    # Report-only: the eval step must not fail the build on a miss (AC8).
    jobs = doc.get("jobs", {})
    eval_steps = [
        step
        for job in jobs.values()
        for step in job.get("steps", [])
        if "run-pack-evals.py" in str(step.get("run", ""))
    ]
    if not eval_steps:
        fail("no step invokes tools/run-pack-evals.py")
    for step in eval_steps:
        if step.get("continue-on-error") is not True:
            fail("the run-pack-evals.py step must be continue-on-error (report-only)")

    # Artifact upload is the bounded summary.json only — never the per-run
    # outputs/ captures (AC10).
    upload_steps = [
        step
        for job in jobs.values()
        for step in job.get("steps", [])
        if "upload-artifact" in str(step.get("uses", ""))
    ]
    if not upload_steps:
        fail("must upload the activation summaries as an artifact")
    for step in upload_steps:
        path = str(step.get("with", {}).get("path", ""))
        if "summary.json" not in path:
            fail("the artifact path must target summary.json")
        if "outputs" in path:
            fail("the artifact path must EXCLUDE the per-run outputs/ captures (AC10)")

    print("✓ pack-evals.yml: schedule+dispatch only (no push/PR), contents:read, "
          "consumes ANTHROPIC_API_KEY, report-only eval step, bounded summary "
          "artifact (outputs/ excluded). YAML parses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
